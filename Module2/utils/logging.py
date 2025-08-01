from loguru import logger
import sys
import os

def setup_logging():
    logger.remove()
    # Console output
    logger.add(sys.stdout, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # File output - app.log
    logger.add("logs/app.log", rotation="500 MB", level="DEBUG", 
              format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
    
    # File output - image_generator.log
    logger.add("/tmp/image_generator.log", rotation="100 MB", level="INFO",
              format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")
    
    return logger

logger = setup_logging()
