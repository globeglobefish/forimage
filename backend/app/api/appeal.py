"""
Ban Appeal API for users.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.blacklist import Blacklist, BanAppeal, AppealStatus
from app.api.deps import get_current_user

router = APIRouter(prefix="/appeal", tags=["Appeal"])


class AppealCreate(BaseModel):
    reason: str


class AppealResponse(BaseModel):
    id: int
    blacklist_id: int
    reason: str
    status: str
    admin_response: Optional[str]
    handled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BanStatusResponse(BaseModel):
    is_banned: bool
    ban_id: Optional[int] = None
    reason: Optional[str] = None
    ban_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    can_appeal: bool = False
    existing_appeal: Optional[AppealResponse] = None


@router.get("/status", response_model=BanStatusResponse)
async def get_ban_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if current user is banned and get ban details."""
    # Find active ban for this user (only get the most recent one that hasn't been lifted)
    result = await db.execute(
        select(Blacklist).where(
            Blacklist.user_id == user.id,
            Blacklist.lifted_at.is_(None)  # Only active bans
        ).order_by(Blacklist.created_at.desc())
    )
    ban = result.scalars().first()
    
    if not ban or not ban.is_active:
        return BanStatusResponse(is_banned=False)
    
    # Check for existing appeal (get the most recent one)
    appeal_result = await db.execute(
        select(BanAppeal).where(
            BanAppeal.blacklist_id == ban.id,
            BanAppeal.user_id == user.id,
        ).order_by(BanAppeal.created_at.desc())
    )
    existing_appeal = appeal_result.scalars().first()
    
    appeal_response = None
    can_appeal = True
    
    if existing_appeal:
        appeal_response = AppealResponse(
            id=existing_appeal.id,
            blacklist_id=existing_appeal.blacklist_id,
            reason=existing_appeal.reason,
            status=existing_appeal.status.value,
            admin_response=existing_appeal.admin_response,
            handled_at=existing_appeal.handled_at,
            created_at=existing_appeal.created_at,
        )
        # Can only appeal if previous appeal was rejected
        can_appeal = existing_appeal.status == AppealStatus.REJECTED
    
    return BanStatusResponse(
        is_banned=True,
        ban_id=ban.id,
        reason=ban.reason,
        ban_type=ban.ban_type.value,
        expires_at=ban.expires_at,
        can_appeal=can_appeal,
        existing_appeal=appeal_response,
    )


@router.post("", response_model=AppealResponse)
async def create_appeal(
    data: AppealCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a ban appeal."""
    # Find active ban (only get the most recent one that hasn't been lifted)
    result = await db.execute(
        select(Blacklist).where(
            Blacklist.user_id == user.id,
            Blacklist.lifted_at.is_(None)  # Only active bans
        ).order_by(Blacklist.created_at.desc())
    )
    ban = result.scalars().first()
    
    if not ban or not ban.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not currently banned"
        )
    
    # Check for pending appeal
    appeal_result = await db.execute(
        select(BanAppeal).where(
            BanAppeal.blacklist_id == ban.id,
            BanAppeal.user_id == user.id,
            BanAppeal.status == AppealStatus.PENDING,
        )
    )
    existing = appeal_result.scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending appeal"
        )
    
    # Create appeal
    appeal = BanAppeal(
        blacklist_id=ban.id,
        user_id=user.id,
        reason=data.reason,
    )
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)
    
    return AppealResponse(
        id=appeal.id,
        blacklist_id=appeal.blacklist_id,
        reason=appeal.reason,
        status=appeal.status.value,
        admin_response=appeal.admin_response,
        handled_at=appeal.handled_at,
        created_at=appeal.created_at,
    )


@router.get("/history", response_model=List[AppealResponse])
async def get_appeal_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's appeal history."""
    result = await db.execute(
        select(BanAppeal).where(
            BanAppeal.user_id == user.id
        ).order_by(BanAppeal.created_at.desc())
    )
    appeals = result.scalars().all()
    
    return [
        AppealResponse(
            id=a.id,
            blacklist_id=a.blacklist_id,
            reason=a.reason,
            status=a.status.value,
            admin_response=a.admin_response,
            handled_at=a.handled_at,
            created_at=a.created_at,
        )
        for a in appeals
    ]
