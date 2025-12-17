"""
Timezone utility functions for handling system timezone settings.
Converts UTC timestamps to the configured system timezone.
"""
from datetime import datetime, timezone
import pytz
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Default timezone fallback
DEFAULT_TIMEZONE = "Asia/Shanghai"

# Cache for timezone object and name
_tz_cache: Optional[pytz.timezone] = None
_tz_name_cache: Optional[str] = None


async def get_system_timezone() -> pytz.timezone:
    """
    Get the system timezone object from settings.
    
    Returns:
        pytz timezone object
    
    Note:
        This function caches the timezone object for performance.
        Call refresh_timezone_cache() when timezone setting changes.
    """
    global _tz_cache, _tz_name_cache
    
    if _tz_cache is not None:
        return _tz_cache
    
    try:
        from app.services.settings import get_timezone
        tz_name = await get_timezone()
        
        if not tz_name:
            tz_name = DEFAULT_TIMEZONE
            logger.warning(f"Empty timezone setting, using default: {DEFAULT_TIMEZONE}")
        
        try:
            _tz_cache = pytz.timezone(tz_name)
            _tz_name_cache = tz_name
            logger.info(f"System timezone set to: {tz_name}")
            return _tz_cache
        except pytz.exceptions.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {tz_name}, falling back to {DEFAULT_TIMEZONE}")
            _tz_cache = pytz.timezone(DEFAULT_TIMEZONE)
            _tz_name_cache = DEFAULT_TIMEZONE
            return _tz_cache
            
    except Exception as e:
        logger.warning(f"Failed to get timezone from settings: {e}, using {DEFAULT_TIMEZONE}")
        _tz_cache = pytz.timezone(DEFAULT_TIMEZONE)
        _tz_name_cache = DEFAULT_TIMEZONE
        return _tz_cache


def refresh_timezone_cache():
    """
    Refresh the timezone cache (call when timezone setting changes).
    
    This should be called whenever the timezone setting is updated
    to ensure the new timezone takes effect immediately.
    """
    global _tz_cache, _tz_name_cache
    old_tz = _tz_name_cache
    _tz_cache = None
    _tz_name_cache = None
    logger.info(f"Timezone cache cleared (was: {old_tz})")


async def convert_to_system_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert a UTC datetime to system timezone.
    
    Args:
        dt: UTC datetime object (or naive datetime assumed to be UTC)
    
    Returns:
        Datetime in system timezone
    
    Note:
        If timezone conversion fails, returns the original datetime.
    """
    if dt is None:
        return None
    
    try:
        # If datetime is naive, assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        
        # Convert to system timezone
        tz = await get_system_timezone()
        return dt.astimezone(tz)
    except Exception as e:
        logger.warning(f"Failed to convert datetime to system timezone: {e}")
        return dt


async def get_current_time() -> datetime:
    """
    Get current time in system timezone.
    
    Returns:
        Current datetime in system timezone
    
    Note:
        If timezone retrieval fails, returns current local time.
    """
    try:
        tz = await get_system_timezone()
        return datetime.now(tz)
    except Exception as e:
        logger.warning(f"Failed to get current time in system timezone: {e}, using local time")
        return datetime.now()


async def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime in system timezone.
    
    Args:
        dt: Datetime to format (UTC or naive)
        fmt: Format string
    
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return ""
    
    converted = await convert_to_system_timezone(dt)
    if converted is None:
        return ""
    
    return converted.strftime(fmt)


async def format_datetime_iso(dt: Optional[datetime]) -> str:
    """Format datetime as ISO string in system timezone."""
    if dt is None:
        return ""
    
    converted = await convert_to_system_timezone(dt)
    if converted is None:
        return ""
    
    return converted.isoformat()
