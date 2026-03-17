# graph/state.py
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # ── Stage 1: Raw inputs from the user ──────────────────────
    resume_text: str          # Raw text extracted from resume PDF
    jd_text: str              # Job description pasted by user
    company_name: str         # Target company name

    # ── Stage 2: Processed context (filled by prep agents) ─────
    resume_chunks: List[str]  # Resume split into chunks for RAG
    jd_skills: Dict           # Extracted skills, level, keywords
    company_context: Dict     # Tech stack, culture, news

    # ── Stage 3: Interview data (filled during loop) ────────────
    question_bank: List[Dict] # 15 generated questions
    current_question_index: int  # Which question we are on (0-14)
    current_round: str        # "technical" or "hr"
    conversation_history: List[Dict]  # All Q&A pairs so far
    scores: List[Dict]        # STAR scores for each answer

    # ── Stage 4: Control flags ──────────────────────────────────
    is_complete: bool         # True when all questions answered
    error_message: Optional[str]  # Stores any error that occurs

    # ── Stage 5: Final output ───────────────────────────────────
    report_html: str          # Final HTML report content