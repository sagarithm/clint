import logging
import sys
from rich.logging import RichHandler

def setup_logger(name: str = "ColdMailer"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)]
    )
    return logging.getLogger(name)

logger = setup_logger()
