"""
Logging Configuration
Provides structured logging with multiple output formats and handlers.
"""

import logging
import sys
import json
from pathlib import Path
from typing import Any, Optional, cast
from logging.handlers import RotatingFileHandler
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        extra_fields = cast("dict[str, Any] | None", getattr(record, "extra_fields", None))
        if isinstance(extra_fields, dict):
            log_data.update(extra_fields)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Custom colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format
            
        Returns:
            Colored log string
        """
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build log message
        log_msg = f"{color}[{timestamp}] {record.levelname:8s}{reset} "
        log_msg += f"{record.name} - {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"
        
        return log_msg


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    output: str = "both",
    log_file: Optional[str] = None,
    max_file_size_mb: int = 100,
    backup_count: int = 5
) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        output: Output destination ('console', 'file', or 'both')
        log_file: Path to log file
        max_file_size_mb: Maximum log file size in MB
        backup_count: Number of backup files to keep
    """
    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Choose formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = ColoredFormatter()
    
    # Add console handler
    if output in ["console", "both"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler
    if output in ["file", "both"] and log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        max_bytes = max_file_size_mb * 1024 * 1024
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        
        # Use JSON formatter for file output
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)
    
    # Log initial message
    root_logger.info(f"Logging initialized - Level: {level}, Format: {log_format}, Output: {output}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra fields to log records."""
    
    def __init__(self, logger: logging.Logger, **extra_fields):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            **extra_fields: Extra fields to add to log records
        """
        self.logger = logger
        self.extra_fields = extra_fields
        self.old_factory = None
    
    def __enter__(self) -> "LogContext":
        """Enter context and add extra fields."""
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            if self.old_factory is None:
                raise RuntimeError("Log record factory is not initialized")
            record = self.old_factory(*args, **kwargs)
            setattr(record, "extra_fields", self.extra_fields)
            return record

        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and restore original factory."""
        if self.old_factory is not None:
            logging.setLogRecordFactory(self.old_factory)


# Example usage:
# with LogContext(logger, request_id="12345", user_id="user@example.com"):
#     logger.info("Processing request")

# Made with Bob
