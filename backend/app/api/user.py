from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.image import Image
from app.models.album import Album
from app.schemas.user import UserResponse, UserUpdate
from app.api.deps import get_current_user
from app.utils.security import get_password_hash, verify_password
from pydantic import BaseModel

router = APIRouter(prefix="/user", tags=["User"])


class UserStats(BaseModel):
    total_images: int
    total_albums: int
    total_storage_used: int  # in bytes


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
):
    """Get current user information."""
    return UserResponse.model_validate(user)


@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's statistics."""
    # Count images
    image_count_result = await db.execute(
        select(func.count()).select_from(Image).where(Image.user_id == user.id)
    )
    total_images = image_count_result.scalar()
    
    # Count albums
    album_count_result = await db.execute(
        select(func.count()).select_from(Album).where(Album.user_id == user.id)
    )
    total_albums = album_count_result.scalar()
    
    # Sum storage used
    storage_result = await db.execute(
        select(func.sum(Image.file_size)).where(Image.user_id == user.id)
    )
    total_storage = storage_result.scalar() or 0
    
    return UserStats(
        total_images=total_images,
        total_albums=total_albums,
        total_storage_used=total_storage,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user information."""
    # Check if username is taken
    if data.username and data.username != user.username:
        result = await db.execute(
            select(User).where(User.username == data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = data.username
    
    # Check if email is taken
    if data.email and data.email != user.email:
        result = await db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        user.email = data.email
        # TODO: Re-verify email?
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    import re
    
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确"
        )
    
    # 验证新密码强度
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少8位"
        )
    if not re.search(r'[a-z]', data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码必须包含小写字母"
        )
    if not re.search(r'[A-Z]', data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码必须包含大写字母"
        )
    if not re.search(r'\d', data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码必须包含数字"
        )
    
    # 检查新密码不能与旧密码相同
    if verify_password(data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与当前密码相同"
        )
    
    user.hashed_password = get_password_hash(data.new_password)
    await db.commit()
    
    return {"message": "密码修改成功"}
