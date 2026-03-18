# utils/logger.py
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

# ── Create logs directory ────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

# ── Log format ───────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger for any module.
    Usage: logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Console handler (colored) ────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColorFormatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console)

    # ── File handler (rotating, max 5MB, keep 3 backups) ─────────
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # Don't propagate to root logger
    logger.propagate = False

    return logger


class ColorFormatter(logging.Formatter):
    """Adds colors to console output based on log level."""

    COLORS = {
        "DEBUG":    "\033[36m",   # Cyan
        "INFO":     "\033[32m",   # Green
        "WARNING":  "\033[33m",   # Yellow
        "ERROR":    "\033[31m",   # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    BOLD  = "\033[1m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{self.BOLD}{record.levelname}{self.RESET}"
        return super().format(record)


class SessionLogger:
    """
    A wrapper that automatically includes session_id in every log message.
    Usage:
        log = SessionLogger("resume_parser", session_id)
        log.info("Processing started")
        # Output: [abc12345] Processing started
    """
    def __init__(self, module_name: str, session_id: str = ""):
        self._logger = get_logger(module_name)
        self._session = f"[{session_id}] " if session_id else ""

    def info(self, msg: str):    self._logger.info(self._session + msg)
    def debug(self, msg: str):   self._logger.debug(self._session + msg)
    def warning(self, msg: str): self._logger.warning(self._session + msg)
    def error(self, msg: str):   self._logger.error(self._session + msg)
    def critical(self, msg: str):self._logger.critical(self._session + msg)


def log_agent_start(logger, agent_name: str, session_id: str = ""):
    """Standard log when an agent starts."""
    prefix = f"[{session_id}] " if session_id else ""
    logger.info(f"{prefix}{'='*10} {agent_name.upper()} STARTED {'='*10}")


def log_agent_end(logger, agent_name: str, duration_ms: int, session_id: str = ""):
    """Standard log when an agent finishes with duration."""
    prefix = f"[{session_id}] " if session_id else ""
    logger.info(f"{prefix}{'='*10} {agent_name.upper()} DONE in {duration_ms}ms {'='*10}")