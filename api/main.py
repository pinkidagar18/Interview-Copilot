# api/main.py
import os
import uuid
import time
import threading
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Optional
import tempfile
from dotenv import load_dotenv

load_dotenv()

# ── Logging + Exceptions ─────────────────────────────────────────
from utils.logger import get_logger, SessionLogger
from utils.exceptions import (
    InterviewCopilotError,
    SessionNotFoundError,
    SessionAlreadyCompleteError,
    MissingResumeError,
    MissingJobDescriptionError,
    MissingCompanyNameError,
    InvalidFileTypeError,
    EmptyAnswerError,
    ReportNotReadyError,
    LLMConnectionError,
    LLMQuotaError,
    QuestionGenerationError,
)
from utils.notifier import send_notification

# ── Agents ───────────────────────────────────────────────────────
from agents.resume_parser import resume_parser_node, load_resume_from_pdf
from agents.jd_analyzer import jd_analyzer_node
from agents.web_researcher import web_researcher_node
from agents.question_generator import question_generator_node
from agents.interviewer import interviewer_node, submit_answer
from agents.answer_evaluator import evaluator_node
from agents.report_generator import report_generator_node
from graph.state import AgentState

logger = get_logger("api.main")

# ════════════════════════════════════════════════════════
# APP INIT
# ════════════════════════════════════════════════════════
app = FastAPI(
    title="InterviewCopilot API",
    description="AI-powered personalised interview coach",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store ──────────────────────────────────────
sessions: dict = {}


# ════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ════════════════════════════════════════════════════════
class StartRequest(BaseModel):
    jd_text: str
    company_name: str
    resume_text: Optional[str] = ""

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class SessionResponse(BaseModel):
    session_id: str
    message: str
    current_question: Optional[str] = None
    question_number: Optional[int] = None
    total_questions: Optional[int] = None
    question_type: Optional[str] = None
    round: Optional[str] = None

class ScoreResponse(BaseModel):
    session_id: str
    scores: dict
    next_question: Optional[str] = None
    question_number: Optional[int] = None
    is_complete: bool
    message: str


# ════════════════════════════════════════════════════════
# GLOBAL EXCEPTION HANDLERS
# ════════════════════════════════════════════════════════
@app.exception_handler(InterviewCopilotError)
async def interview_copilot_exception_handler(request: Request, exc: InterviewCopilotError):
    """Handles all custom InterviewCopilot exceptions cleanly."""
    logger.error(f"[{exc.code}] {exc.message} | Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors with clean messages."""
    errors = []
    for e in exc.errors():
        field = " → ".join(str(x) for x in e["loc"])
        errors.append(f"{field}: {e['msg']}")
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "code": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "details": errors
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches any unhandled exception — last line of defense."""
    logger.critical(
        f"Unhandled exception on {request.url.path}: "
        f"{type(exc).__name__}: {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again.",
            "detail": str(exc)
        }
    )


# ════════════════════════════════════════════════════════
# REQUEST LOGGING MIDDLEWARE
# ════════════════════════════════════════════════════════
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs every incoming request and its response time."""
    start = time.time()
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(
        f"← {request.method} {request.url.path} "
        f"| {response.status_code} | {duration}ms"
    )
    return response


# ════════════════════════════════════════════════════════
# HELPER
# ════════════════════════════════════════════════════════
def get_current_question_text(state: AgentState) -> Optional[str]:
    """Extract the last interviewer message from conversation history."""
    history = state.get("conversation_history", [])
    for msg in reversed(history):
        if msg.get("role") == "interviewer":
            return msg.get("content")
    return None


# ════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════

# ── Serve HTML UI ────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main HTML frontend from templates/index.html"""
    html_path = os.path.join("templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            logger.debug("Serving index.html")
            return HTMLResponse(content=f.read())
    logger.warning("index.html not found in templates/")
    return HTMLResponse(
        content="<h1>UI not found. Place index.html in templates/</h1>",
        status_code=404
    )


# ── Health check ─────────────────────────────────────────────────
@app.get("/health")
def health():
    """Quick health check endpoint."""
    logger.info("Health check OK")
    return {
        "status": "ok",
        "message": "InterviewCopilot API is running!",
        "version": "1.0.0",
        "active_sessions": len(sessions),
    }


# ── Upload resume PDF ────────────────────────────────────────────
@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a PDF resume and extract text."""
    logger.info(f"Resume upload received: {file.filename} ({file.content_type})")

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise InvalidFileTypeError(file.filename)

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        t = time.time()
        resume_text = load_resume_from_pdf(tmp_path)
        ms = round((time.time() - t) * 1000)
        os.unlink(tmp_path)

        logger.info(
            f"Resume extracted: {len(resume_text):,} chars "
            f"from '{file.filename}' in {ms}ms"
        )
        return {
            "resume_text": resume_text,
            "character_count": len(resume_text),
            "message": "Resume extracted successfully"
        }

    except InterviewCopilotError:
        os.unlink(tmp_path)
        raise

    except Exception as e:
        os.unlink(tmp_path)
        logger.error(f"Resume extraction failed for '{file.filename}': {e}")
        raise InterviewCopilotError(
            message=f"Could not extract text from PDF: {str(e)}",
            code="PDF_EXTRACTION_ERROR",
            status_code=422
        )


# ── Start interview ──────────────────────────────────────────────
@app.post("/start", response_model=SessionResponse)
async def start_interview(request: StartRequest):
    """
    Start a new interview session.
    Runs all 3 prep agents + question generator + first question.
    """

    # ── Input validation ─────────────────────────────────────────
    if not request.resume_text or not request.resume_text.strip():
        raise MissingResumeError()
    if not request.jd_text or not request.jd_text.strip():
        raise MissingJobDescriptionError()
    if not request.company_name or not request.company_name.strip():
        raise MissingCompanyNameError()

    session_id = str(uuid.uuid4())[:8]
    log = SessionLogger("api.start", session_id)
    t_total = time.time()

    log.info(
        f"New session started | "
        f"Company: {request.company_name} | "
        f"Resume: {len(request.resume_text):,} chars | "
        f"JD: {len(request.jd_text):,} chars"
    )

    # ── Build initial state ──────────────────────────────────────
    state: AgentState = {
        "resume_text": request.resume_text,
        "jd_text": request.jd_text,
        "company_name": request.company_name,
        "resume_chunks": [],
        "jd_skills": {},
        "company_context": {},
        "question_bank": [],
        "current_question_index": 0,
        "current_round": "technical",
        "conversation_history": [],
        "scores": [],
        "is_complete": False,
        "error_message": None,
        "report_html": ""
    }

    # ── Run all prep agents with timing ─────────────────────────
    agents = [
        ("Resume Parser",      resume_parser_node),
        ("JD Analyzer",        jd_analyzer_node),
        ("Web Researcher",     web_researcher_node),
        ("Question Generator", question_generator_node),
        ("Interviewer",        interviewer_node),
    ]

    for agent_name, agent_fn in agents:
        t = time.time()
        log.info(f"Running {agent_name}...")
        try:
            state = agent_fn(state)
            ms = round((time.time() - t) * 1000)
            log.info(f"{agent_name} completed in {ms}ms")

        except Exception as e:
            ms = round((time.time() - t) * 1000)
            log.error(
                f"{agent_name} failed after {ms}ms: "
                f"{type(e).__name__}: {e}"
            )
            # Detect specific LLM errors
            err_str = str(e).lower()
            if "quota" in err_str or "429" in err_str or "rate" in err_str:
                raise LLMQuotaError("Groq")
            if "connection" in err_str or "timeout" in err_str or "unreachable" in err_str:
                raise LLMConnectionError("Groq")
            # Generic agent error
            raise InterviewCopilotError(
                message=f"{agent_name} failed: {str(e)}",
                code=f"{agent_name.upper().replace(' ', '_')}_ERROR",
                status_code=500
            )

    # ── Validate question bank ───────────────────────────────────
    if not state["question_bank"]:
        log.error("Question bank is empty after generation")
        raise QuestionGenerationError("No questions were generated. Please try again.")

    # ── Store session ────────────────────────────────────────────
    sessions[session_id] = state
    total_ms = round((time.time() - t_total) * 1000)
    total_q = len(state["question_bank"])

    log.info(
        f"Session ready | "
        f"{total_q} questions generated | "
        f"Total time: {total_ms}ms"
    )

    return SessionResponse(
        session_id=session_id,
        message="Interview started successfully",
        current_question=get_current_question_text(state),
        question_number=1,
        total_questions=total_q,
        question_type=state["question_bank"][0]["type"],
        round=state["current_round"]
    )


# ── Submit answer ────────────────────────────────────────────────
@app.post("/answer", response_model=ScoreResponse)
async def submit_candidate_answer(request: AnswerRequest):
    """
    Submit candidate answer, evaluate with STAR scoring,
    then ask next question or generate report if done.
    """

    # ── Validate ─────────────────────────────────────────────────
    if not request.answer or not request.answer.strip():
        raise EmptyAnswerError()

    if request.session_id not in sessions:
        raise SessionNotFoundError(request.session_id)

    state = sessions[request.session_id]
    log = SessionLogger("api.answer", request.session_id)

    if state.get("is_complete"):
        raise SessionAlreadyCompleteError(request.session_id)

    current_idx = state.get("current_question_index", 0)
    total = len(state.get("question_bank", []))

    log.info(
        f"Answer received for Q{current_idx + 1}/{total} "
        f"| {len(request.answer):,} chars"
    )

    try:
        # ── Evaluate answer ──────────────────────────────────────
        t = time.time()
        state = submit_answer(state, request.answer)
        state = evaluator_node(state)
        ms = round((time.time() - t) * 1000)

        latest_score = state["scores"][-1] if state["scores"] else {}
        overall = latest_score.get("overall", 0)

        log.info(
            f"Q{current_idx + 1} evaluated | "
            f"Score: {overall}/10 | "
            f"S:{latest_score.get('S',0)} "
            f"T:{latest_score.get('T',0)} "
            f"A:{latest_score.get('A',0)} "
            f"R:{latest_score.get('R',0)} | "
            f"{ms}ms"
        )

        # ── Build score payload ──────────────────────────────────
        score_payload = {
            "S":               latest_score.get("S", 0),
            "T":               latest_score.get("T", 0),
            "A":               latest_score.get("A", 0),
            "R":               latest_score.get("R", 0),
            "overall":         latest_score.get("overall", 0),
            "good":            latest_score.get("good", ""),
            "missing":         latest_score.get("missing", ""),
            "question_type":   latest_score.get("question_type", ""),
            "candidate_answer":latest_score.get("candidate_answer", ""),
        }

        # ── Interview complete → generate report ─────────────────
        if state.get("is_complete"):
            log.info("All questions answered — generating report...")
            t = time.time()
            state = report_generator_node(state)
            ms = round((time.time() - t) * 1000)
            sessions[request.session_id] = state

            # Calculate final stats for log
            all_scores = state.get("scores", [])
            avg = round(
                sum(s.get("overall", 0) for s in all_scores) / len(all_scores), 1
            ) if all_scores else 0

            log.info(
                f"Report generated in {ms}ms | "
                f"Final avg score: {avg}/10 ({round(avg*10)}%)"
            )

            return ScoreResponse(
                session_id=request.session_id,
                scores=score_payload,
                next_question=None,
                question_number=None,
                is_complete=True,
                message="Interview complete! Download your report."
            )

        # ── Not complete → ask next question ─────────────────────
        state = interviewer_node(state)
        sessions[request.session_id] = state

        next_q = get_current_question_text(state)
        next_idx = state["current_question_index"]

        log.info(f"Moving to Q{next_idx + 1}/{total}")

        return ScoreResponse(
            session_id=request.session_id,
            scores=score_payload,
            next_question=next_q,
            question_number=next_idx + 1,
            is_complete=False,
            message=f"Q{next_idx + 1} of {total}"
        )

    except InterviewCopilotError:
        raise

    except Exception as e:
        log.error(f"Answer processing failed: {type(e).__name__}: {e}")
        raise InterviewCopilotError(
            message=f"Failed to process your answer: {str(e)}",
            code="ANSWER_PROCESSING_ERROR",
            status_code=500
        )


# ── Get status ───────────────────────────────────────────────────
@app.get("/status/{session_id}")
def get_status(session_id: str):
    """Get current interview status for a session."""
    if session_id not in sessions:
        raise SessionNotFoundError(session_id)

    state = sessions[session_id]
    total = len(state.get("question_bank", []))
    current = state.get("current_question_index", 0)

    logger.debug(
        f"Status check [{session_id}]: "
        f"{current}/{total} | "
        f"complete={state.get('is_complete', False)}"
    )

    return {
        "session_id":    session_id,
        "is_complete":   state.get("is_complete", False),
        "current_question": current,
        "total_questions":  total,
        "progress_pct":  round((current / total * 100) if total > 0 else 0),
        "current_round": state.get("current_round", "technical"),
        "scores_so_far": len(state.get("scores", [])),
    }


# ── Get report + send notification ──────────────────────────────
@app.get("/report/{session_id}")
def get_report(session_id: str):
    """Download the PDF/HTML report and send email notification."""
    if session_id not in sessions:
        raise SessionNotFoundError(session_id)

    state = sessions[session_id]

    if not state.get("is_complete"):
        answered = state.get("current_question_index", 0)
        total = len(state.get("question_bank", []))
        raise ReportNotReadyError(session_id, answered, total)

    logger.info(f"Report download requested [{session_id}]")

    # ── Send email notification in background (non-blocking) ─────
    # User gets their file immediately, email sends silently
    threading.Thread(
        target=send_notification,
        args=(session_id, state),
        daemon=True
    ).start()
    logger.info(f"Notification thread started [{session_id}]")

    # ── Return PDF if exists ─────────────────────────────────────
    pdf_path = "outputs/interview_report.pdf"
    if os.path.exists(pdf_path):
        logger.info(f"Serving PDF report [{session_id}]")
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"interview_report_{session_id}.pdf"
        )

    # ── Fallback to HTML ─────────────────────────────────────────
    html_path = "outputs/report.html"
    if os.path.exists(html_path):
        logger.info(f"Serving HTML report [{session_id}] (PDF not found)")
        return FileResponse(
            path=html_path,
            media_type="text/html",
            filename=f"interview_report_{session_id}.html"
        )

    # ── Fallback to JSON scores ──────────────────────────────────
    logger.warning(f"No report file found [{session_id}] — returning JSON scores")
    scores = state.get("scores", [])
    avg = sum(s.get("overall", 0) for s in scores) / len(scores) if scores else 0
    return {
        "session_id":     session_id,
        "overall_score":  round(avg, 1),
        "readiness_pct":  round(avg * 10),
        "total_questions": len(scores),
        "scores":         scores
    }


# ── Clear session ────────────────────────────────────────────────
@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear a session from memory."""
    if session_id not in sessions:
        raise SessionNotFoundError(session_id)
    del sessions[session_id]
    logger.info(f"Session cleared: {session_id}")
    return {"message": f"Session {session_id} cleared successfully"}


# ── List active sessions (admin) ─────────────────────────────────
@app.get("/admin/sessions")
def list_sessions():
    """List all active sessions — for monitoring."""
    summary = []
    for sid, state in sessions.items():
        scores = state.get("scores", [])
        avg = round(
            sum(s.get("overall", 0) for s in scores) / len(scores), 1
        ) if scores else 0
        summary.append({
            "session_id":    sid,
            "company":       state.get("company_name", ""),
            "is_complete":   state.get("is_complete", False),
            "questions_done": len(scores),
            "total_questions": len(state.get("question_bank", [])),
            "avg_score":     avg,
        })
    logger.info(f"Admin: {len(summary)} active sessions")
    return {"active_sessions": len(summary), "sessions": summary}