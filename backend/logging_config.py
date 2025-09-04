"""
Comprehensive logging configuration for debugging
"""
import logging
import sys
from datetime import datetime

def setup_detailed_logging():
    """Setup detailed logging for debugging"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Application specific loggers
    app_loggers = [
        'app',
        'app.api',
        'app.api.quiz',
        'app.services',
        'app.services.quiz_service',
        'app.models',
        'app.core',
        'sqlalchemy.engine',
        'uvicorn',
        'uvicorn.access'
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
    
    # SQLAlchemy SQL logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
    
    print(f"[{datetime.now()}] Detailed logging configured")
    print("Logging levels:")
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        print(f"  {logger_name}: {logger.level}")

if __name__ == "__main__":
    setup_detailed_logging()
