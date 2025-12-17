"""
Date path utility for generating date-based folder paths.
Used for organizing uploaded images into YYYY/MM/DD folder structure.
"""
from datetime import datetime
from typing import Optional
import pytz
import logging

logger = logging.getLogger(__name__)

# Default timezone fallback
DEFAULT_TIMEZONE = "Asia/Shanghai"


async def get_date_path(dt: Optional[datetime] = None) -> str:
    """
    Generate date path string in YYYY/MM/DD format.
    
    Args:
        dt: Optional datetime to use. If None, uses current time in system timezone.
    
    Returns:
        Date path string in format "YYYY/MM/DD" (e.g., "2025/12/14")
    
    Note:
        This function is designed to be robust - it will always return a valid
        date path even if timezone operations fail.
    """
    try:
        if dt is None:
            # Get current time in system timezone
            try:
                from app.utils.timezone import get_current_time
                dt = await get_current_time()
            except Exception as e:
                logger.warning(f"Failed to get current time from timezone service: {e}, using local time")
                try:
                    tz = pytz.timezone(DEFAULT_TIMEZONE)
                    dt = datetime.now(tz)
                except Exception:
                    dt = datetime.now()
        elif dt.tzinfo is None:
            # If naive datetime, assume it's in system timezone
            try:
                from app.utils.timezone import get_system_timezone
                tz = await get_system_timezone()
                dt = tz.localize(dt)
            except Exception as e:
                logger.warning(f"Failed to localize datetime: {e}")
                # Keep the naive datetime as-is
        
        # Format as YYYY/MM/DD
        return dt.strftime("%Y/%m/%d")
    except Exception as e:
        # Ultimate fallback - should never happen but ensures we always return a valid path
        logger.error(f"Unexpected error in get_date_path: {e}, using current local time")
        return datetime.now().strftime("%Y/%m/%d")


def get_date_path_sync(dt: Optional[datetime] = None, timezone_name: str = None) -> str:
    """
    Synchronous version of get_date_path for use in non-async contexts.
    
    Args:
        dt: Optional datetime to use. If None, uses current time.
        timezone_name: Timezone name to use (default: Asia/Shanghai)
    
    Returns:
        Date path string in format "YYYY/MM/DD" (e.g., "2025/12/14")
    
    Note:
        This function is designed to be robust - it will always return a valid
        date path even if timezone operations fail.
    """
    if timezone_name is None:
        timezone_name = DEFAULT_TIMEZONE
    
    try:
        if dt is None:
            try:
                tz = pytz.timezone(timezone_name)
                dt = datetime.now(tz)
            except Exception as e:
                logger.warning(f"Failed to get timezone {timezone_name}: {e}, using local time")
                dt = datetime.now()
        elif dt.tzinfo is None:
            # If naive datetime, assume it's in the specified timezone
            try:
                tz = pytz.timezone(timezone_name)
                dt = tz.localize(dt)
            except Exception as e:
                logger.warning(f"Failed to localize datetime with {timezone_name}: {e}")
                # Keep the naive datetime as-is
        
        # Format as YYYY/MM/DD
        return dt.strftime("%Y/%m/%d")
    except Exception as e:
        # Ultimate fallback
        logger.error(f"Unexpected error in get_date_path_sync: {e}, using current local time")
        return datetime.now().strftime("%Y/%m/%d")


def build_file_path(date_path: str, filename: str) -> str:
    """
    Build full file path by combining date path and filename.
    
    Args:
        date_path: Date path string (e.g., "2025/12/14")
        filename: Filename with extension (e.g., "abc123.png")
    
    Returns:
        Full file path (e.g., "2025/12/14/abc123.png")
    
    Note:
        Handles edge cases like empty date_path or filename with leading/trailing slashes.
    """
    # Sanitize inputs
    date_path = (date_path or "").strip().strip("/")
    filename = (filename or "").strip().strip("/")
    
    if not date_path:
        return filename
    if not filename:
        return date_path
    
    return f"{date_path}/{filename}"


def validate_date_path(path: str) -> bool:
    """
    Validate that a path looks like a valid date path (YYYY/MM/DD format).
    
    Args:
        path: Path string to validate
    
    Returns:
        True if path matches YYYY/MM/DD format, False otherwise
    """
    if not path:
        return False
    
    parts = path.split("/")
    if len(parts) != 3:
        return False
    
    try:
        year, month, day = parts
        # Validate year (reasonable range)
        if not (2020 <= int(year) <= 2100):
            return False
        # Validate month
        if not (1 <= int(month) <= 12):
            return False
        # Validate day
        if not (1 <= int(day) <= 31):
            return False
        return True
    except (ValueError, TypeError):
        return False


def extract_date_from_path(file_path: str) -> Optional[str]:
    """
    Extract date path from a full file path.
    
    Args:
        file_path: Full file path (e.g., "2025/12/14/abc123.png")
    
    Returns:
        Date path string (e.g., "2025/12/14") or None if not a date-based path
    """
    if not file_path:
        return None
    
    parts = file_path.split("/")
    if len(parts) >= 4:
        # Assume format: YYYY/MM/DD/filename
        potential_date = "/".join(parts[:3])
        if validate_date_path(potential_date):
            return potential_date
    
    return None
