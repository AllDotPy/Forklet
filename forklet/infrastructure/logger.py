import logging
import sys
from typing import Optional, Union


def setup_logger(
    name: str = "Forklet",
    level: Union[int, str] = logging.INFO,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger.
    
    Args:
        name: Logger name
        level: Logging level
        log_format: Log message format
        log_file: Path to log file
        console: Enable console output
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Set logging level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Default format
    if log_format is None:
        log_format = "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


####    GLOBAL LOGGER INSTANCE
logger = setup_logger("Forklet")