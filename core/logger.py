import logging
import os
import re
from typing import Optional
from rich.logging import RichHandler


class RedactionFilter(logging.Filter):
    """Redacts likely secret patterns from log messages before output."""

    PATTERNS = [
        re.compile(r"(OPENROUTER_API_KEY\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
        re.compile(r"(SMTP_PASS_\d+\s*[=:]\s*)([^\s,;]+)", re.IGNORECASE),
        re.compile(r"(Authorization['\"]?\s*[:=]\s*['\"]?Bearer\s+)([^'\"\s,;]+)", re.IGNORECASE),
        re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]+\b"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
            redacted = message
            for pattern in self.PATTERNS:
                if pattern.groups >= 2:
                    redacted = pattern.sub(r"\1***REDACTED***", redacted)
                else:
                    redacted = pattern.sub("***REDACTED***", redacted)
            record.msg = redacted
            record.args = ()
        except Exception:
            pass
        return True

def setup_logger(name: str = "Clint") -> logging.Logger:
    """
    Configures and returns a structured logger using Rich for console 
    and a traditional FileHandler for persistent auditing.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup is called multiple times
    if logger.hasHandlers():
        return logger

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "outreach.log")

    # Console Handler: Beautiful, interactive output
    console_handler = RichHandler(
        rich_tracebacks=True, 
        markup=True, 
        show_time=True, 
        show_path=False
    )
    console_handler.addFilter(RedactionFilter())
    
    # File Handler: Persistent record of all activities
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    file_handler.addFilter(RedactionFilter())

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    
    logger.setLevel(logging.INFO)
    return logger

# Singleton instance for the entire application
logger = setup_logger()
