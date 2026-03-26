import logging
import os
from typing import Optional
from rich.logging import RichHandler

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
    
    # File Handler: Persistent record of all activities
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    
    logger.setLevel(logging.INFO)
    return logger

# Singleton instance for the entire application
logger = setup_logger()
