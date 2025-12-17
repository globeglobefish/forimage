from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models.user import User, UserStatus
from app.models.image import Image, ImageStatus
from app.api.deps import get_admin_user

router = APIRouter()


class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    pending_users: int
    disabled_users: int
    total_images: int
    approved_images: int
    pending_images: int
    rejected_images: int
    total_storage_bytes: int
    today_uploads: int
    today_registrations: int


class DailyStats(BaseModel):
    date: str
    uploads: int
    registrations: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    daily_stats: List[DailyStats]


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get admin dashboard statistics."""
    # User stats
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    active_users = (await db.execute(
        select(func.count()).select_from(User).where(User.status == UserStatus.ACTIVE)
    )).scalar()
    pending_users = (await db.execute(
        select(func.count()).select_from(User).where(User.status == UserStatus.PENDING)
    )).scalar()
    disabled_users = (await db.execute(
        select(func.count()).select_from(User).where(User.status == UserStatus.DISABLED)
    )).scalar()
    
    # Image stats
    total_images = (await db.execute(select(func.count()).select_from(Image))).scalar()
    approved_images = (await db.execute(
        select(func.count()).select_from(Image).where(Image.status == ImageStatus.APPROVED)
    )).scalar()
    pending_images = (await db.execute(
        select(func.count()).select_from(Image).where(Image.status == ImageStatus.PENDING)
    )).scalar()
    rejected_images = (await db.execute(
        select(func.count()).select_from(Image).where(Image.status == ImageStatus.REJECTED)
    )).scalar()
    
    # Storage stats
    total_storage = (await db.execute(
        select(func.sum(Image.file_size))
    )).scalar() or 0
    
    # Today stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_uploads = (await db.execute(
        select(func.count()).select_from(Image).where(Image.created_at >= today_start)
    )).scalar()
    today_registrations = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )).scalar()
    
    # Daily stats for last 30 days
    daily_stats = []
    for i in range(30):
        date = datetime.utcnow().date() - timedelta(days=i)
        day_start = datetime.combine(date, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        
        uploads = (await db.execute(
            select(func.count()).select_from(Image)
            .where(Image.created_at >= day_start, Image.created_at < day_end)
        )).scalar()
        
        registrations = (await db.execute(
            select(func.count()).select_from(User)
            .where(User.created_at >= day_start, User.created_at < day_end)
        )).scalar()
        
        daily_stats.append(DailyStats(
            date=date.isoformat(),
            uploads=uploads,
            registrations=registrations,
        ))
    
    daily_stats.reverse()  # Oldest first
    
    return DashboardResponse(
        stats=DashboardStats(
            total_users=total_users,
            active_users=active_users,
            pending_users=pending_users,
            disabled_users=disabled_users,
            total_images=total_images,
            approved_images=approved_images,
            pending_images=pending_images,
            rejected_images=rejected_images,
            total_storage_bytes=total_storage,
            today_uploads=today_uploads,
            today_registrations=today_registrations,
        ),
        daily_stats=daily_stats,
    )
