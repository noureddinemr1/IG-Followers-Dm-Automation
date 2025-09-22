"""
Logging Configuration for Instagram Scraper
Provides structured logging with multiple handlers and formatters
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json

from config.settings import get_setting

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'target_username'):
            log_data['target_username'] = record.target_username
        if hasattr(record, 'scrape_type'):
            log_data['scrape_type'] = record.scrape_type
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        # Create colored level name
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)

def setup_logging(
    log_level: str = None,
    log_file: str = None,
    enable_json: bool = True,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        enable_json: Enable JSON formatting for file logs
        enable_console: Enable console logging
        
    Returns:
        Configured logger instance
    """
    
    # Get settings
    log_level = log_level or get_setting('logging.level', 'INFO')
    log_file = log_file or get_setting('logging.file', '/app/logs/scraper.log')
    max_size = get_setting('logging.max_size', 10485760)  # 10MB
    backup_count = get_setting('logging.backup_count', 5)
    
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        if enable_json:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
        
        root_logger.addHandler(file_handler)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if os.getenv('ENVIRONMENT') == 'development':
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s'
            )
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Error file handler (separate file for errors)
    error_file = str(log_path).replace('.log', '_errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter() if enable_json else file_formatter)
    root_logger.addHandler(error_handler)
    
    # Return main application logger
    return logging.getLogger('instagram_scraper')

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f"instagram_scraper.{name}")

def log_scraping_event(
    logger: logging.Logger,
    event_type: str,
    target_username: str,
    details: Dict[str, Any],
    level: str = 'INFO'
):
    """
    Log a scraping event with structured data
    
    Args:
        logger: Logger instance
        event_type: Type of event (start, success, error, etc.)
        target_username: Target Instagram username
        details: Additional event details
        level: Log level
    """
    extra = {
        'target_username': target_username,
        'scrape_type': event_type,
        **details
    }
    
    log_level = getattr(logging, level.upper())
    logger.log(log_level, f"Scraping event: {event_type} for @{target_username}", extra=extra)

def log_performance(
    logger: logging.Logger,
    operation: str,
    execution_time: float,
    details: Dict[str, Any] = None
):
    """
    Log performance metrics
    
    Args:
        logger: Logger instance
        operation: Operation name
        execution_time: Execution time in seconds
        details: Additional details
    """
    extra = {
        'execution_time': execution_time,
        **(details or {})
    }
    
    logger.info(f"Performance: {operation} completed in {execution_time:.2f}s", extra=extra)

# Context manager for timing operations
class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, logger: logging.Logger, operation: str, details: Dict[str, Any] = None):
        self.logger = logger
        self.operation = operation
        self.details = details or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        execution_time = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            log_performance(self.logger, self.operation, execution_time, self.details)
        else:
            self.logger.error(
                f"Operation failed: {self.operation} after {execution_time:.2f}s",
                extra={'execution_time': execution_time, **self.details},
                exc_info=True
            )

# Application-specific loggers
def get_main_logger() -> logging.Logger:
    """Get main application logger"""
    return get_logger('main')

def get_scraper_logger() -> logging.Logger:
    """Get scraper logger"""
    return get_logger('scraper')

def get_auth_logger() -> logging.Logger:
    """Get authentication logger"""
    return get_logger('auth')

def get_scheduler_logger() -> logging.Logger:
    """Get scheduler logger"""
    return get_logger('scheduler')

def get_health_logger() -> logging.Logger:
    """Get health check logger"""
    return get_logger('health')

# Initialize logging on import
if not logging.getLogger().handlers:
    setup_logging()

# Export commonly used functions
__all__ = [
    'setup_logging',
    'get_logger',
    'log_scraping_event',
    'log_performance',
    'TimingContext',
    'get_main_logger',
    'get_scraper_logger',
    'get_auth_logger',
    'get_scheduler_logger',
    'get_health_logger'
]