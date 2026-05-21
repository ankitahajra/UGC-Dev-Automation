"""
Utility Functions
Common utility functions used across the pipeline.
"""

import time
import functools
from typing import Any, Callable, Optional, TypeVar, cast
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_multiplier: Multiplier for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


def timeout(seconds: int) -> Callable:
    """
    Decorator to add timeout to functions.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            import signal
            
            def timeout_handler(signum: int, frame: Any) -> None:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Set the signal handler and alarm
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm
                signal.alarm(0)
            
            return result
        
        return wrapper
    return decorator


def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object as string.
    
    Args:
        dt: Datetime object (defaults to current time)
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string
        format_str: Format string
        
    Returns:
        Datetime object
    """
    return datetime.strptime(timestamp_str, format_str)


def calculate_time_difference(start: datetime, end: Optional[datetime] = None) -> timedelta:
    """
    Calculate time difference between two timestamps.
    
    Args:
        start: Start timestamp
        end: End timestamp (defaults to current time)
        
    Returns:
        Time difference as timedelta
    """
    if end is None:
        end = datetime.utcnow()
    return end - start


def format_duration(duration: timedelta) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        duration: Duration as timedelta
        
    Returns:
        Formatted duration string
    """
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string by removing special characters and limiting length.
    
    Args:
        text: Input text
        max_length: Maximum length (optional)
        
    Returns:
        Sanitized string
    """
    # Remove special characters except alphanumeric, dash, and underscore
    sanitized = ''.join(c if c.isalnum() or c in ['-', '_'] else '-' for c in text)
    
    # Remove consecutive dashes
    while '--' in sanitized:
        sanitized = sanitized.replace('--', '-')
    
    # Trim dashes from start and end
    sanitized = sanitized.strip('-')
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-')
    
    return sanitized.lower()


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: Input list
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    Flatten nested dictionary.
    
    Args:
        d: Input dictionary
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_get(d: dict, key_path: str, default: Any = None) -> Any:
    """
    Safely get value from nested dictionary using dot notation.
    
    Args:
        d: Input dictionary
        key_path: Dot-separated key path
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    keys = key_path.split('.')
    value = d
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def merge_dicts(*dicts: dict) -> dict:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def validate_required_fields(data: dict, required_fields: list) -> tuple[bool, list]:
    """
    Validate that required fields are present in dictionary.
    
    Args:
        data: Input dictionary
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, missing_fields)
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    return len(missing_fields) == 0, missing_fields


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

# Made with Bob
