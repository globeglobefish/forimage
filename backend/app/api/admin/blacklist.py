from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.blacklist import Blacklist, ViolationLog, BanAppeal, BanType, AppealStatus
from app.api.deps import get_admin_user
from app.services.security import create_ban, remove_ban

router = APIRouter(prefix="/blacklist")


# ============================================================================
# Schemas
# ============================================================================

class BlacklistResponse(BaseModel):
    id: int
    ip_address: Optional[str]
    user_id: Optional[int]
    username: Optional[str] = None
    reason: str
    ban_type: str
    expires_at: Optional[datetime]
    violation_count: int
    is_active: bool
    created_at: datetime
    # Lift info
    lifted_at: Optional[datetime] = None
    lifted_by: Optional[int] = None
    lift_reason: Optional[str] = None

    class Config:
        from_attributes = True


class BlacklistCreate(BaseModel):
    ip_address: Optional[str] = None
    user_id: Optional[int] = None
    reason: str
    ban_type: str = "TEMPORARY"
    duration_minutes: int = 1440


class ViolationResponse(BaseModel):
    id: int
    ip_address: str
    user_id: Optional[int]
    username: Optional[str] = None
    image_id: Optional[int]
    violation_type: str
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AppealResponse(BaseModel):
    id: int
    blacklist_id: int
    user_id: int
    username: str
    reason: str
    status: str
    admin_response: Optional[str]
    handled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AppealHandle(BaseModel):
    status: str
    admin_response: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int


# ============================================================================
# STATIC ROUTES - Must be defined BEFORE dynamic routes like /{ban_id}
# ============================================================================

@router.get("", response_model=PaginatedResponse)
async def get_blacklist(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    active_only: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated blacklist."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Parse active_only from string
    is_active_only = active_only in ('true', 'True', '1', 'yes')
    logger.info(f"get_blacklist: active_only={active_only}, is_active_only={is_active_only}")
    
    query = select(Blacklist).options(selectinload(Blacklist.user))
    count_query = select(func.count(Blacklist.id))
    
    if search:
        query = query.where(
            or_(
                Blacklist.ip_address.contains(search),
                Blacklist.reason.contains(search),
            )
        )
        count_query = count_query.where(
            or_(
                Blacklist.ip_address.contains(search),
                Blacklist.reason.contains(search),
            )
        )
    
    if is_active_only:
        from sqlalchemy import and_
        now = datetime.utcnow()
        # Active = not lifted AND (permanent OR not expired)
        active_condition = and_(
            Blacklist.lifted_at.is_(None),
            or_(
                Blacklist.ban_type == BanType.PERMANENT,
                Blacklist.expires_at > now,
                Blacklist.expires_at.is_(None)
            )
        )
        query = query.where(active_condition)
        count_query = count_query.where(active_condition)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(Blacklist.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    bans = result.scalars().all()
    
    items = []
    for ban in bans:
        item = BlacklistResponse(
            id=ban.id,
            ip_address=ban.ip_address,
            user_id=ban.user_id,
            reason=ban.reason,
            ban_type=ban.ban_type.value,
            expires_at=ban.expires_at,
            violation_count=ban.violation_count,
            is_active=ban.is_active,
            created_at=ban.created_at,
            lifted_at=ban.lifted_at,
            lifted_by=ban.lifted_by,
            lift_reason=ban.lift_reason,
        )
        if ban.user:
            item.username = ban.user.username
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=BlacklistResponse)
async def create_blacklist_entry(
    data: BlacklistCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new blacklist entry."""
    if not data.ip_address and not data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide ip_address or user_id"
        )
    
    ban_type = BanType.PERMANENT if data.ban_type.upper() == "PERMANENT" else BanType.TEMPORARY
    
    ban = await create_ban(
        ip=data.ip_address,
        user_id=data.user_id,
        reason=data.reason,
        ban_type=ban_type,
        duration_minutes=data.duration_minutes,
        created_by=admin.id,
        db=db
    )
    
    return BlacklistResponse(
        id=ban.id,
        ip_address=ban.ip_address,
        user_id=ban.user_id,
        reason=ban.reason,
        ban_type=ban.ban_type.value,
        expires_at=ban.expires_at,
        violation_count=ban.violation_count,
        is_active=ban.is_active,
        created_at=ban.created_at,
    )


@router.get("/stats")
async def get_blacklist_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get blacklist statistics."""
    now = datetime.utcnow()
    
    total_result = await db.execute(select(func.count(Blacklist.id)))
    total_bans = total_result.scalar()
    
    # Active bans: not lifted AND (permanent OR not expired)
    from sqlalchemy import and_
    active_result = await db.execute(
        select(func.count(Blacklist.id)).where(
            and_(
                Blacklist.lifted_at.is_(None),  # Not lifted
                or_(
                    Blacklist.ban_type == BanType.PERMANENT,
                    Blacklist.expires_at > now,
                    Blacklist.expires_at.is_(None)
                )
            )
        )
    )
    active_bans = active_result.scalar()
    
    since_24h = now - timedelta(hours=24)
    violations_result = await db.execute(
        select(func.count(ViolationLog.id)).where(
            ViolationLog.created_at >= since_24h
        )
    )
    violations_24h = violations_result.scalar()
    
    appeals_result = await db.execute(
        select(func.count(BanAppeal.id)).where(
            BanAppeal.status == AppealStatus.PENDING
        )
    )
    pending_appeals = appeals_result.scalar()
    
    return {
        "total_bans": total_bans,
        "active_bans": active_bans,
        "violations_24h": violations_24h,
        "pending_appeals": pending_appeals,
    }


@router.get("/violations", response_model=PaginatedResponse)
async def get_violations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    violation_type: Optional[str] = None,
    ip_address: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated violation logs."""
    query = select(ViolationLog).options(selectinload(ViolationLog.user))
    count_query = select(func.count(ViolationLog.id))
    
    if violation_type:
        query = query.where(ViolationLog.violation_type == violation_type)
        count_query = count_query.where(ViolationLog.violation_type == violation_type)
    
    if ip_address:
        query = query.where(ViolationLog.ip_address == ip_address)
        count_query = count_query.where(ViolationLog.ip_address == ip_address)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(ViolationLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    violations = result.scalars().all()
    
    items = []
    for v in violations:
        item = ViolationResponse(
            id=v.id,
            ip_address=v.ip_address,
            user_id=v.user_id,
            image_id=v.image_id,
            violation_type=v.violation_type,
            details=v.details,
            created_at=v.created_at,
        )
        if v.user:
            item.username = v.user.username
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/appeals", response_model=PaginatedResponse)
async def get_appeals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated ban appeals."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"get_appeals: status_filter={status_filter}")
    
    query = select(BanAppeal).options(selectinload(BanAppeal.user))
    count_query = select(func.count(BanAppeal.id))
    
    # Only filter if status_filter is provided and not empty
    if status_filter and status_filter.strip():
        try:
            appeal_status = AppealStatus(status_filter.upper())
            query = query.where(BanAppeal.status == appeal_status)
            count_query = count_query.where(BanAppeal.status == appeal_status)
            logger.info(f"Filtering by status: {appeal_status}")
        except ValueError as e:
            logger.warning(f"Invalid status_filter: {status_filter}, error: {e}")
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(BanAppeal.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    appeals = result.scalars().all()
    
    items = []
    for a in appeals:
        item = AppealResponse(
            id=a.id,
            blacklist_id=a.blacklist_id,
            user_id=a.user_id,
            username=a.user.username if a.user else "Unknown",
            reason=a.reason,
            status=a.status.value,
            admin_response=a.admin_response,
            handled_at=a.handled_at,
            created_at=a.created_at,
        )
        items.append(item)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.put("/appeals/{appeal_id}")
async def handle_appeal(
    appeal_id: int,
    data: AppealHandle,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle a ban appeal (approve or reject)."""
    result = await db.execute(
        select(BanAppeal).where(BanAppeal.id == appeal_id)
    )
    appeal = result.scalar_one_or_none()
    
    if not appeal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appeal not found"
        )
    
    if appeal.status != AppealStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appeal already handled"
        )
    
    appeal.status = AppealStatus.APPROVED if data.status.upper() == "APPROVED" else AppealStatus.REJECTED
    appeal.admin_response = data.admin_response
    appeal.handled_by = admin.id
    appeal.handled_at = datetime.utcnow()
    
    if appeal.status == AppealStatus.APPROVED:
        await remove_ban(appeal.blacklist_id, db, lifted_by=admin.id, lift_reason="申诉通过")
    
    await db.commit()
    
    return {"message": f"Appeal {data.status}"}


# ============================================================================
# DYNAMIC ROUTES - Must be defined AFTER static routes
# ============================================================================

@router.delete("/{ban_id}")
async def delete_blacklist_entry(
    ban_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Lift a blacklist entry (unban) - marks as lifted, preserves history."""
    success = await remove_ban(ban_id, db, lifted_by=admin.id, lift_reason="管理员手动解封")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ban not found"
        )
    return {"message": "Ban lifted successfully"}


@router.put("/{ban_id}/extend")
async def extend_ban(
    ban_id: int,
    minutes: int = Query(..., ge=1),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Extend a temporary ban."""
    result = await db.execute(
        select(Blacklist).where(Blacklist.id == ban_id)
    )
    ban = result.scalar_one_or_none()
    
    if not ban:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ban not found"
        )
    
    if ban.ban_type == BanType.PERMANENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot extend permanent ban"
        )
    
    if ban.expires_at:
        ban.expires_at = ban.expires_at + timedelta(minutes=minutes)
    else:
        ban.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
    
    await db.commit()
    
    return {"message": f"Ban extended by {minutes} minutes", "new_expires_at": ban.expires_at}


@router.put("/{ban_id}/permanent")
async def make_permanent(
    ban_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert a temporary ban to permanent."""
    result = await db.execute(
        select(Blacklist).where(Blacklist.id == ban_id)
    )
    ban = result.scalar_one_or_none()
    
    if not ban:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ban not found"
        )
    
    ban.ban_type = BanType.PERMANENT
    ban.expires_at = None
    await db.commit()
    
    return {"message": "Ban is now permanent"}
