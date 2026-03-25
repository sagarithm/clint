import logging
import sys
import os
from rich.logging import RichHandler

def setup_logger(name: str = "ColdMailer"):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True),
            logging.FileHandler(os.path.join(log_dir, "outreach.log"), encoding="utf-8")
        ]
    )
    return logging.getLogger(name)

logger = setup_logger()
