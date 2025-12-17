from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from typing import Optional
from app.redis import get_redis

limiter = Limiter(key_func=get_remote_address)

# Cache for IP header settings (to avoid async calls in sync context)
_ip_header_cache = {
    "header": "X-Forwarded-For",
    "trust_proxy": True,
}


def update_ip_header_cache(header: str, trust_proxy: bool):
    """Update the IP header cache (called from async context)."""
    global _ip_header_cache
    _ip_header_cache["header"] = header
    _ip_header_cache["trust_proxy"] = trust_proxy


def get_real_ip(request: Request) -> str:
    """
    Get the real client IP address, considering proxies.
    
    Supports multiple header formats:
    - X-Forwarded-For: Standard proxy header (comma-separated, first is client)
    - X-Real-IP: Nginx real IP header
    - CF-Connecting-IP: Cloudflare connecting IP
    - True-Client-IP: Akamai/Cloudflare Enterprise
    """
    if not _ip_header_cache["trust_proxy"]:
        # Don't trust proxy headers, use direct connection
        if request.client:
            return request.client.host
        return "unknown"
    
    configured_header = _ip_header_cache["header"]
    
    # Try the configured header first
    if configured_header:
        header_value = request.headers.get(configured_header)
        if header_value:
            # X-Forwarded-For can contain multiple IPs, take the first one
            if "," in header_value:
                return header_value.split(",")[0].strip()
            return header_value.strip()
    
    # Fallback: try common headers in order of preference
    # CF-Connecting-IP is most reliable for Cloudflare
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    
    # True-Client-IP (Cloudflare Enterprise / Akamai)
    true_client_ip = request.headers.get("True-Client-IP")
    if true_client_ip:
        return true_client_ip.strip()
    
    # X-Real-IP (Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # X-Forwarded-For (standard proxy header)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Fallback to direct connection IP
    if request.client:
        return request.client.host
    
    return "unknown"


async def refresh_ip_header_settings():
    """Refresh IP header settings from database."""
    from app.services import settings as settings_service
    header = await settings_service.get_real_ip_header()
    trust_proxy = await settings_service.is_trust_proxy_enabled()
    update_ip_header_cache(header, trust_proxy)


async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int, int]:
    """
    Check rate limit using Redis.
    Returns: (is_allowed, current_count, remaining)
    """
    redis = get_redis()
    if not redis:
        return True, 0, limit

    redis_key = f"rate_limit:{key}"
    
    # Use Redis pipeline for atomic operations
    pipe = redis.pipeline()
    pipe.incr(redis_key)
    pipe.expire(redis_key, window_seconds)
    results = await pipe.execute()
    
    current_count = results[0]
    remaining = max(0, limit - current_count)
    is_allowed = current_count <= limit

    return is_allowed, current_count, remaining


async def get_upload_rate_limit_key(request: Request, user_id: Optional[int] = None) -> str:
    """Generate rate limit key for uploads."""
    if user_id:
        return f"upload:user:{user_id}"
    return f"upload:ip:{get_real_ip(request)}"


async def check_login_attempts(ip: str) -> tuple[bool, int]:
    """
    Check failed login attempts for an IP.
    Returns: (is_blocked, attempts_count)
    """
    redis = get_redis()
    if not redis:
        return False, 0

    key = f"login_attempts:{ip}"
    attempts = await redis.get(key)
    
    if attempts is None:
        return False, 0
    
    attempts = int(attempts)
    # Block if more than 5 failed attempts in 15 minutes
    return attempts >= 5, attempts


async def record_failed_login(ip: str):
    """Record a failed login attempt."""
    redis = get_redis()
    if not redis:
        return

    key = f"login_attempts:{ip}"
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 900)  # 15 minutes
    await pipe.execute()


async def clear_login_attempts(ip: str):
    """Clear failed login attempts after successful login."""
    redis = get_redis()
    if not redis:
        return

    key = f"login_attempts:{ip}"
    await redis.delete(key)


async def add_to_blacklist(ip: str, duration_seconds: int = 3600):
    """Add IP to temporary blacklist."""
    redis = get_redis()
    if not redis:
        return

    key = f"blacklist:{ip}"
    await redis.setex(key, duration_seconds, "1")


async def is_blacklisted(ip: str) -> bool:
    """Check if IP is blacklisted."""
    redis = get_redis()
    if not redis:
        return False

    key = f"blacklist:{ip}"
    return await redis.exists(key) > 0
