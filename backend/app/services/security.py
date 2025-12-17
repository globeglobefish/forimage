"""
Security Service
Handles blacklist checking, violation logging, and automatic banning.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timedelta
from typing import Optional, Tuple
import json
import logging

from app.models.blacklist import Blacklist, ViolationLog, BanType
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# In-memory cache for rate limiting (simple implementation)
# Format: {key: [(timestamp, count), ...]}
_rate_cache = {}


async def is_banned(ip: str, user_id: Optional[int] = None, db: AsyncSession = None) -> Tuple[bool, Optional[str]]:
    """
    Check if IP or user is banned.
    Returns: (is_banned, reason)
    """
    close_db = False
    if db is None:
        db = AsyncSessionLocal()
        close_db = True
    
    try:
        # Build query conditions - only check active bans (not lifted)
        conditions = []
        if ip:
            conditions.append(Blacklist.ip_address == ip)
        if user_id:
            conditions.append(Blacklist.user_id == user_id)
        
        if not conditions:
            return False, None
        
        # Query blacklist - get all matching active bans, ordered by most recent
        result = await db.execute(
            select(Blacklist).where(
                and_(
                    or_(*conditions),
                    Blacklist.lifted_at.is_(None)  # Only active bans
                )
            ).order_by(Blacklist.created_at.desc())
        )
        bans = result.scalars().all()
        
        if not bans:
            return False, None
        
        # Check each ban to find an active one
        for ban in bans:
            # Check if ban is still active
            if ban.ban_type == BanType.PERMANENT:
                return True, ban.reason
            
            if ban.expires_at and datetime.utcnow() < ban.expires_at:
                return True, ban.reason
        
        # All bans expired
        return False, None
    finally:
        if close_db:
            await db.close()


async def log_violation(
    ip: str,
    violation_type: str,
    user_id: Optional[int] = None,
    image_id: Optional[int] = None,
    details: Optional[dict] = None,
    db: AsyncSession = None
) -> ViolationLog:
    """Log a violation and check if auto-ban should be triggered."""
    close_db = False
    if db is None:
        db = AsyncSessionLocal()
        close_db = True
    
    try:
        # Create violation log
        violation = ViolationLog(
            ip_address=ip,
            user_id=user_id,
            image_id=image_id,
            violation_type=violation_type,
            details=json.dumps(details) if details else None,
        )
        db.add(violation)
        await db.commit()
        await db.refresh(violation)
        
        # Check if auto-ban should be triggered
        await check_auto_ban(ip, user_id, violation_type, db)
        
        return violation
    finally:
        if close_db:
            await db.close()


async def check_auto_ban(
    ip: str,
    user_id: Optional[int],
    violation_type: str,
    db: AsyncSession
):
    """Check if automatic ban should be triggered based on violation history."""
    from app.services.settings import (
        get_setting_bool,
        get_setting_int,
    )
    
    # Check if auto-ban is enabled
    if not await get_setting_bool("security_auto_ban_enabled", True):
        return
    
    # Get thresholds
    if violation_type == "audit_failed":
        threshold = await get_setting_int("security_audit_fail_threshold", 3)
    else:  # rate_limit_exceeded
        threshold = await get_setting_int("security_rate_exceed_threshold", 3)
    
    ban_duration_minutes = await get_setting_int("security_temp_ban_duration", 1440)  # Default 24 hours in minutes
    
    # Count recent violations (last 24 hours)
    since = datetime.utcnow() - timedelta(hours=24)
    
    conditions = [
        ViolationLog.violation_type == violation_type,
        ViolationLog.created_at >= since,
    ]
    
    if user_id:
        conditions.append(ViolationLog.user_id == user_id)
    else:
        conditions.append(ViolationLog.ip_address == ip)
    
    result = await db.execute(
        select(func.count(ViolationLog.id)).where(and_(*conditions))
    )
    count = result.scalar()
    
    # Trigger auto-ban if threshold reached
    if count >= threshold:
        # Use English for ban reason to support i18n on frontend
        await create_ban(
            ip=ip,
            user_id=user_id,
            reason=f"Auto-ban: {violation_type} violations reached {count} times",
            ban_type=BanType.TEMPORARY,
            duration_minutes=ban_duration_minutes,
            db=db
        )
        logger.warning(f"Auto-banned IP={ip} user_id={user_id} for {violation_type} for {ban_duration_minutes} minutes")


async def create_ban(
    ip: Optional[str],
    user_id: Optional[int],
    reason: str,
    ban_type: BanType = BanType.TEMPORARY,
    duration_minutes: int = 1440,  # Default 24 hours in minutes
    created_by: Optional[int] = None,
    db: AsyncSession = None
) -> Blacklist:
    """Create a new ban entry."""
    close_db = False
    if db is None:
        db = AsyncSessionLocal()
        close_db = True
    
    try:
        # Check if already banned
        conditions = []
        if ip:
            conditions.append(Blacklist.ip_address == ip)
        if user_id:
            conditions.append(Blacklist.user_id == user_id)
        
        if conditions:
            # Find active (not lifted) ban for this IP/user
            result = await db.execute(
                select(Blacklist).where(
                    and_(
                        or_(*conditions),
                        Blacklist.lifted_at.is_(None)  # Only match active bans
                    )
                ).order_by(Blacklist.created_at.desc())
            )
            existing = result.scalars().first()
            
            if existing:
                # Update existing active ban
                existing.reason = reason
                existing.ban_type = ban_type
                existing.violation_count += 1
                if ban_type == BanType.TEMPORARY:
                    existing.expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
                else:
                    existing.expires_at = None
                await db.commit()
                await db.refresh(existing)
                return existing
        
        # Create new ban
        expires_at = None
        if ban_type == BanType.TEMPORARY:
            expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        ban = Blacklist(
            ip_address=ip,
            user_id=user_id,
            reason=reason,
            ban_type=ban_type,
            expires_at=expires_at,
            created_by=created_by,
        )
        db.add(ban)
        await db.commit()
        await db.refresh(ban)
        return ban
    finally:
        if close_db:
            await db.close()


async def remove_ban(
    ban_id: int, 
    db: AsyncSession,
    lifted_by: Optional[int] = None,
    lift_reason: Optional[str] = None
) -> bool:
    """Lift a ban by ID (marks as lifted, does not delete)."""
    result = await db.execute(
        select(Blacklist).where(Blacklist.id == ban_id)
    )
    ban = result.scalar_one_or_none()
    
    if not ban:
        return False
    
    # Mark as lifted instead of deleting
    ban.lifted_at = datetime.utcnow()
    ban.lifted_by = lifted_by
    ban.lift_reason = lift_reason or "手动解封"
    await db.commit()
    return True


async def check_rate_limit_multi(
    ip: str,
    user_id: Optional[int],
    is_user: bool
) -> Tuple[bool, str, int]:
    """
    Check multiple rate limits (per minute, hour, day).
    Returns: (is_allowed, limit_type, remaining)
    """
    from app.services.settings import get_setting_int
    from app.utils.rate_limit import check_rate_limit
    
    # Get limits from settings
    if is_user:
        per_minute = await get_setting_int("security_rate_limit_user_per_minute", 10)
        per_hour = await get_setting_int("security_rate_limit_user_per_hour", 100)
        per_day = await get_setting_int("security_rate_limit_user_per_day", 500)
        key_prefix = f"upload:user:{user_id}"
    else:
        per_minute = await get_setting_int("security_rate_limit_guest_per_minute", 3)
        per_hour = await get_setting_int("security_rate_limit_guest_per_hour", 10)
        per_day = await get_setting_int("security_rate_limit_guest_per_day", 30)
        key_prefix = f"upload:ip:{ip}"
    
    # Check per-minute limit (60 seconds window)
    allowed, count, remaining = await check_rate_limit(f"{key_prefix}:minute", per_minute, 60)
    if not allowed:
        return False, "minute", remaining
    
    # Check per-hour limit (3600 seconds window)
    allowed, count, remaining = await check_rate_limit(f"{key_prefix}:hour", per_hour, 3600)
    if not allowed:
        return False, "hour", remaining
    
    # Check per-day limit (86400 seconds window)
    allowed, count, remaining = await check_rate_limit(f"{key_prefix}:day", per_day, 86400)
    if not allowed:
        return False, "day", remaining
    
    return True, "", remaining


async def get_violation_count(
    ip: str,
    user_id: Optional[int],
    violation_type: str,
    hours: int = 24,
    db: AsyncSession = None
) -> int:
    """Get violation count for IP/user in the specified time window."""
    close_db = False
    if db is None:
        db = AsyncSessionLocal()
        close_db = True
    
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        conditions = [
            ViolationLog.violation_type == violation_type,
            ViolationLog.created_at >= since,
        ]
        
        if user_id:
            conditions.append(ViolationLog.user_id == user_id)
        else:
            conditions.append(ViolationLog.ip_address == ip)
        
        result = await db.execute(
            select(func.count(ViolationLog.id)).where(and_(*conditions))
        )
        return result.scalar()
    finally:
        if close_db:
            await db.close()
