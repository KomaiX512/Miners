from loguru import logger
import sys
import os

def setup_logging():
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/app.log", rotation="500 MB", level="DEBUG")
    return logger

logger = setup_logging()
