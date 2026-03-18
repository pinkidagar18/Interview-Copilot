# utils/exceptions.py
from fastapi import HTTPException
from typing import Optional


# ════════════════════════════════════════════════════════
# BASE EXCEPTION
# ════════════════════════════════════════════════════════
class InterviewCopilotError(Exception):
    """Base exception for all InterviewCopilot errors."""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self):
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code
        }


# ════════════════════════════════════════════════════════
# SESSION ERRORS
# ════════════════════════════════════════════════════════
class SessionNotFoundError(InterviewCopilotError):
    """Raised when a session ID does not exist."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found. It may have expired or never existed.",
            code="SESSION_NOT_FOUND",
            status_code=404
        )

class SessionAlreadyCompleteError(InterviewCopilotError):
    """Raised when trying to answer a question in a completed interview."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' is already complete. Use /report to get your results.",
            code="SESSION_ALREADY_COMPLETE",
            status_code=400
        )

class SessionExpiredError(InterviewCopilotError):
    """Raised when a session has expired."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' has expired. Please start a new interview.",
            code="SESSION_EXPIRED",
            status_code=410
        )


# ════════════════════════════════════════════════════════
# INPUT ERRORS
# ════════════════════════════════════════════════════════
class MissingResumeError(InterviewCopilotError):
    """Raised when no resume is provided."""
    def __init__(self):
        super().__init__(
            message="Resume text is required. Please upload a PDF or paste your resume text.",
            code="MISSING_RESUME",
            status_code=422
        )

class MissingJobDescriptionError(InterviewCopilotError):
    """Raised when no job description is provided."""
    def __init__(self):
        super().__init__(
            message="Job description is required. Please paste the full job description.",
            code="MISSING_JD",
            status_code=422
        )

class MissingCompanyNameError(InterviewCopilotError):
    """Raised when no company name is provided."""
    def __init__(self):
        super().__init__(
            message="Company name is required.",
            code="MISSING_COMPANY",
            status_code=422
        )

class InvalidFileTypeError(InterviewCopilotError):
    """Raised when an invalid file type is uploaded."""
    def __init__(self, filename: str):
        super().__init__(
            message=f"File '{filename}' is not supported. Only PDF files are accepted.",
            code="INVALID_FILE_TYPE",
            status_code=415
        )

class EmptyAnswerError(InterviewCopilotError):
    """Raised when candidate submits an empty answer."""
    def __init__(self):
        super().__init__(
            message="Answer cannot be empty. Please provide a response before submitting.",
            code="EMPTY_ANSWER",
            status_code=422
        )


# ════════════════════════════════════════════════════════
# AGENT ERRORS
# ════════════════════════════════════════════════════════
class ResumeParsingError(InterviewCopilotError):
    """Raised when resume PDF cannot be parsed."""
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"Failed to parse resume PDF. {reason}".strip(),
            code="RESUME_PARSE_ERROR",
            status_code=422
        )

class JDAnalysisError(InterviewCopilotError):
    """Raised when JD analysis fails."""
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"Failed to analyse job description. {reason}".strip(),
            code="JD_ANALYSIS_ERROR",
            status_code=500
        )

class CompanyResearchError(InterviewCopilotError):
    """Raised when company research fails."""
    def __init__(self, company: str, reason: str = ""):
        super().__init__(
            message=f"Failed to research '{company}'. {reason}".strip(),
            code="COMPANY_RESEARCH_ERROR",
            status_code=500
        )

class QuestionGenerationError(InterviewCopilotError):
    """Raised when question generation fails."""
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"Failed to generate interview questions. {reason}".strip(),
            code="QUESTION_GEN_ERROR",
            status_code=500
        )

class AnswerEvaluationError(InterviewCopilotError):
    """Raised when answer evaluation fails."""
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"Failed to evaluate answer. {reason}".strip(),
            code="EVALUATION_ERROR",
            status_code=500
        )

class ReportGenerationError(InterviewCopilotError):
    """Raised when report generation fails."""
    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"Failed to generate report. {reason}".strip(),
            code="REPORT_GEN_ERROR",
            status_code=500
        )


# ════════════════════════════════════════════════════════
# LLM ERRORS
# ════════════════════════════════════════════════════════
class LLMConnectionError(InterviewCopilotError):
    """Raised when LLM API is unreachable."""
    def __init__(self, provider: str = "Groq"):
        super().__init__(
            message=f"Cannot connect to {provider} API. Check your API key and internet connection.",
            code="LLM_CONNECTION_ERROR",
            status_code=503
        )

class LLMQuotaError(InterviewCopilotError):
    """Raised when LLM API quota is exceeded."""
    def __init__(self, provider: str = "Groq"):
        super().__init__(
            message=f"{provider} API quota exceeded. Please wait a moment and try again.",
            code="LLM_QUOTA_ERROR",
            status_code=429
        )

class LLMResponseParseError(InterviewCopilotError):
    """Raised when LLM returns invalid JSON."""
    def __init__(self, agent_name: str):
        super().__init__(
            message=f"Unexpected response format from {agent_name}. Retrying with fallback.",
            code="LLM_PARSE_ERROR",
            status_code=500
        )


# ════════════════════════════════════════════════════════
# REPORT ERRORS
# ════════════════════════════════════════════════════════
class ReportNotReadyError(InterviewCopilotError):
    """Raised when report is requested before interview is complete."""
    def __init__(self, session_id: str, answered: int, total: int):
        super().__init__(
            message=f"Report not ready. Interview is {answered}/{total} questions complete.",
            code="REPORT_NOT_READY",
            status_code=400
        )