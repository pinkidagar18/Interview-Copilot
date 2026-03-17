# api/main.py
import os
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile
from dotenv import load_dotenv

load_dotenv()

# ── Import all agents ────────────────────────────────────────────
from agents.resume_parser import resume_parser_node, load_resume_from_pdf
from agents.jd_analyzer import jd_analyzer_node
from agents.web_researcher import web_researcher_node
from agents.question_generator import question_generator_node
from agents.interviewer import interviewer_node, submit_answer
from agents.answer_evaluator import evaluator_node
from agents.report_generator import report_generator_node
from graph.state import AgentState

# ── FastAPI app ──────────────────────────────────────────────────
app = FastAPI(
    title="InterviewCopilot API",
    description="AI-powered personalized interview coach",
    version="1.0.0"
)

# Allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store ──────────────────────────────────────
# Key: session_id (str) → Value: AgentState (dict)
sessions: dict = {}


# ── Request/Response Models ──────────────────────────────────────
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


# ── Helper: get current question from state ──────────────────────
def get_current_question_text(state: AgentState) -> Optional[str]:
    """Extract the last interviewer message from conversation history."""
    history = state.get("conversation_history", [])
    for msg in reversed(history):
        if msg.get("role") == "interviewer":
            return msg.get("content")
    return None


# ── Routes ───────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "InterviewCopilot API is running!",
        "version": "1.0.0",
        "endpoints": ["/start", "/answer", "/report/{session_id}", "/status/{session_id}"]
    }


@app.post("/start", response_model=SessionResponse)
async def start_interview(request: StartRequest):
    """
    Start a new interview session.
    Runs all 3 prep agents + question generator.
    Returns the first question.
    """
    session_id = str(uuid.uuid4())[:8]  # Short 8-char ID
    print(f"\n🚀 New session started: {session_id}")

    # Build initial state
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

    try:
        # Run prep pipeline
        print(f"[{session_id}] Running Resume Parser...")
        state = resume_parser_node(state)

        print(f"[{session_id}] Running JD Analyzer...")
        state = jd_analyzer_node(state)

        print(f"[{session_id}] Running Web Researcher...")
        state = web_researcher_node(state)

        print(f"[{session_id}] Generating Questions...")
        state = question_generator_node(state)

        if not state["question_bank"]:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate questions"
            )

        # Ask first question
        print(f"[{session_id}] Asking first question...")
        state = interviewer_node(state)

        # Store session
        sessions[session_id] = state

        # Get first question text
        first_question = get_current_question_text(state)
        total = len(state["question_bank"])

        print(f"[{session_id}] ✅ Session ready — {total} questions loaded")

        return SessionResponse(
            session_id=session_id,
            message="Interview started successfully",
            current_question=first_question,
            question_number=1,
            total_questions=total,
            question_type=state["question_bank"][0]["type"],
            round=state["current_round"]
        )

    except Exception as e:
        print(f"[{session_id}] ❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF resume and extract text.
    Returns extracted text to be passed to /start.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        resume_text = load_resume_from_pdf(tmp_path)
        os.unlink(tmp_path)  # Clean up temp file
        return {
            "resume_text": resume_text,
            "character_count": len(resume_text),
            "message": "Resume extracted successfully"
        }
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/answer", response_model=ScoreResponse)
async def submit_candidate_answer(request: AnswerRequest):
    """
    Submit candidate answer for current question.
    Evaluates using STAR scoring.
    Asks next question or marks complete.
    """
    session_id = request.session_id

    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )

    state = sessions[session_id]

    if state.get("is_complete"):
        raise HTTPException(
            status_code=400,
            detail="Interview already complete. Call /report to get results."
        )

    try:
        # Submit answer
        state = submit_answer(state, request.answer)

        # Evaluate answer
        state = evaluator_node(state)

        # Get latest score
        latest_score = state["scores"][-1] if state["scores"] else {}

        if state.get("is_complete"):
            # Generate report
            print(f"[{session_id}] Interview complete — generating report...")
            state = report_generator_node(state)
            sessions[session_id] = state

            return ScoreResponse(
                session_id=session_id,
                scores={
                    "S": latest_score.get("S", 0),
                    "T": latest_score.get("T", 0),
                    "A": latest_score.get("A", 0),
                    "R": latest_score.get("R", 0),
                    "overall": latest_score.get("overall", 0),
                    "good": latest_score.get("good", ""),
                    "missing": latest_score.get("missing", "")
                },
                next_question=None,
                question_number=None,
                is_complete=True,
                message="Interview complete! Call /report to download your results."
            )

        # Ask next question
        state = interviewer_node(state)
        sessions[session_id] = state

        next_question = get_current_question_text(state)
        current_index = state["current_question_index"]
        total = len(state["question_bank"])

        return ScoreResponse(
            session_id=session_id,
            scores={
                "S": latest_score.get("S", 0),
                "T": latest_score.get("T", 0),
                "A": latest_score.get("A", 0),
                "R": latest_score.get("R", 0),
                "overall": latest_score.get("overall", 0),
                "good": latest_score.get("good", ""),
                "missing": latest_score.get("missing", "")
            },
            next_question=next_question,
            question_number=current_index + 1,
            is_complete=False,
            message=f"Answer evaluated. Question {current_index + 1} of {total}"
        )

    except Exception as e:
        print(f"[{session_id}] ❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{session_id}")
def get_status(session_id: str):
    """Get current interview status for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]
    total = len(state.get("question_bank", []))
    current = state.get("current_question_index", 0)

    return {
        "session_id": session_id,
        "is_complete": state.get("is_complete", False),
        "current_question": current,
        "total_questions": total,
        "progress_pct": round((current / total * 100) if total > 0 else 0),
        "current_round": state.get("current_round", "technical"),
        "scores_so_far": len(state.get("scores", []))
    }


@app.get("/report/{session_id}")
def get_report(session_id: str):
    """Download the PDF report for a completed interview."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = sessions[session_id]

    if not state.get("is_complete"):
        raise HTTPException(
            status_code=400,
            detail="Interview not complete yet"
        )

    pdf_path = "outputs/interview_report.pdf"
    html_path = "outputs/report.html"

    if os.path.exists(pdf_path):
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"interview_report_{session_id}.pdf"
        )
    elif os.path.exists(html_path):
        return FileResponse(
            path=html_path,
            media_type="text/html",
            filename=f"interview_report_{session_id}.html"
        )
    else:
        # Return score summary as JSON fallback
        scores = state.get("scores", [])
        avg = sum(s.get("overall", 0) for s in scores) / len(scores) if scores else 0
        return {
            "session_id": session_id,
            "overall_score": round(avg, 1),
            "readiness_pct": round(avg * 10),
            "total_questions": len(scores),
            "scores": scores
        }


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear a session from memory."""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    raise HTTPException(status_code=404, detail="Session not found")