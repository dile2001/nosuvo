"""
Logging configuration for NoSubvo
Handles application logs, error tracking, and debugging
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

def setup_logging(app_name='nosuvo', log_level=None):
    """
    Setup application logging with multiple handlers
    
    Args:
        app_name: Name of the application (used for log files)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    log_level_value = getattr(logging, log_level, logging.INFO)
    
    # Create formatter
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_value)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # 2. Application Log File (all logs)
    app_log_file = LOGS_DIR / f'{app_name}_app.log'
    app_file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    app_file_handler.setLevel(logging.DEBUG)
    app_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_file_handler)
    
    # 3. Error Log File (errors and critical only)
    error_log_file = LOGS_DIR / f'{app_name}_error.log'
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # 4. Daily Log File (rotates daily)
    daily_log_file = LOGS_DIR / f'{app_name}_daily.log'
    daily_handler = TimedRotatingFileHandler(
        daily_log_file,
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days
    )
    daily_handler.setLevel(logging.INFO)
    daily_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(daily_handler)
    
    # Log startup message
    logging.info(f"Logging initialized: Level={log_level}, AppName={app_name}")
    logging.info(f"Log files: {LOGS_DIR.absolute()}")
    
    return root_logger

def get_logger(name):
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_exception(logger, message="An exception occurred"):
    """
    Log an exception with full traceback
    
    Args:
        logger: Logger instance
        message: Custom error message
    """
    logger.exception(message)

# Log file paths for reference
def get_log_paths():
    """Get all log file paths"""
    return {
        'directory': str(LOGS_DIR.absolute()),
        'application': str(LOGS_DIR / 'nosuvo_app.log'),
        'errors': str(LOGS_DIR / 'nosuvo_error.log'),
        'daily': str(LOGS_DIR / 'nosuvo_daily.log')
    }

if __name__ == "__main__":
    # Test logging setup
    setup_logging('nosuvo', 'DEBUG')
    
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception:
        log_exception(logger, "Testing exception logging")
    
    print("\n✅ Logging test complete!")
    print(f"\nLog files created in: {LOGS_DIR.absolute()}")
    for name, path in get_log_paths().items():
        print(f"  {name}: {path}")

