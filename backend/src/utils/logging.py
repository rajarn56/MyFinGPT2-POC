import sys
from pathlib import Path
from loguru import logger
from src.config import settings
from src.utils.paths import get_logs_path


def setup_logging():
    """Configure structured logging"""
    logger.remove()  # Remove default handler
    
    # Ensure logs directory exists (under project root)
    logs_dir = get_logs_path()
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # File handler (JSON format for production)
    log_file = logs_dir / "app_{time:YYYY-MM-DD}.log"
    if settings.ENV == "production":
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.LOG_LEVEL,
            rotation="00:00",
            retention="30 days",
            serialize=True  # JSON format
        )
    else:
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.LOG_LEVEL,
            rotation="00:00",
            retention="7 days"
        )

