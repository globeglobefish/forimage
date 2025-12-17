"""
Admin Gallery Management API - 后台画廊管理接口
管理员可以查看和管理所有公开相册
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.album import Album
from app.models.image import Image, ImageStatus
from app.models.user import User
from app.api.deps import get_admin_user

router = APIRouter(prefix="/gallery", tags=["Admin Gallery"])


# Response schemas
class AdminGalleryImageResponse(BaseModel):
    """管理员图片响应"""
    id: int
    filename: str
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminGalleryAlbumResponse(BaseModel):
    """管理员相册响应"""
    id: int
    name: str
    description: Optional[str] = None
    is_public: bool
    image_count: int
    approved_count: int
    owner_id: int
    owner_name: str
    owner_email: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AdminGalleryAlbumDetailResponse(BaseModel):
    """管理员相册详情响应"""
    id: int
    name: str
    description: Optional[str] = None
    is_public: bool
    owner_id: int
    owner_name: str
    owner_email: str
    images: List[AdminGalleryImageResponse]
    total_images: int
    approved_count: int
    pending_count: int
    rejected_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AdminGalleryListResponse(BaseModel):
    """管理员画廊列表响应"""
    albums: List[AdminGalleryAlbumResponse]
    total: int
    page: int
    page_size: int


class AdminGalleryStatsResponse(BaseModel):
    """画廊统计响应"""
    total_public_albums: int
    total_public_images: int
    total_users_with_public_albums: int


class AlbumPublicToggle(BaseModel):
    """切换相册公开状态"""
    is_public: bool


@router.get("/stats", response_model=AdminGalleryStatsResponse)
async def get_gallery_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取画廊统计数据"""
    # 公开相册数量
    public_albums_result = await db.execute(
        select(func.count(Album.id)).where(Album.is_public == True)
    )
    total_public_albums = public_albums_result.scalar() or 0
    
    # 公开相册中的图片数量（只计算已审核通过的）
    public_images_result = await db.execute(
        select(func.count(Image.id))
        .join(Album, Image.album_id == Album.id)
        .where(Album.is_public == True, Image.status == ImageStatus.APPROVED)
    )
    total_public_images = public_images_result.scalar() or 0
    
    # 有公开相册的用户数量
    users_result = await db.execute(
        select(func.count(func.distinct(Album.user_id)))
        .where(Album.is_public == True)
    )
    total_users = users_result.scalar() or 0
    
    return AdminGalleryStatsResponse(
        total_public_albums=total_public_albums,
        total_public_images=total_public_images,
        total_users_with_public_albums=total_users,
    )


@router.get("", response_model=AdminGalleryListResponse)
async def list_public_albums(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    public_only: bool = Query(True, description="只显示公开相册"),
    user_id: Optional[int] = Query(None, description="按用户筛选"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取相册列表（管理员）
    可以查看所有公开相册，或按用户筛选
    """
    offset = (page - 1) * page_size
    
    # 构建查询条件
    conditions = []
    if public_only:
        conditions.append(Album.is_public == True)
    if user_id:
        conditions.append(Album.user_id == user_id)
    
    # 查询总数
    count_query = select(func.count(Album.id))
    if conditions:
        count_query = count_query.where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 查询相册列表
    query = (
        select(Album)
        .options(selectinload(Album.user), selectinload(Album.images))
        .order_by(Album.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if conditions:
        query = query.where(*conditions)
    
    result = await db.execute(query)
    albums = result.scalars().all()
    
    # 构建响应
    album_responses = []
    for album in albums:
        approved_count = sum(
            1 for img in album.images 
            if img.status == ImageStatus.APPROVED
        )
        
        album_responses.append(AdminGalleryAlbumResponse(
            id=album.id,
            name=album.name,
            description=album.description,
            is_public=album.is_public,
            image_count=len(album.images),
            approved_count=approved_count,
            owner_id=album.user_id,
            owner_name=album.user.username if album.user else "Unknown",
            owner_email=album.user.email if album.user else "",
            created_at=album.created_at,
            updated_at=album.updated_at,
        ))
    
    return AdminGalleryListResponse(
        albums=album_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{album_id}", response_model=AdminGalleryAlbumDetailResponse)
async def get_album_detail(
    album_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取相册详情（管理员）"""
    query = (
        select(Album)
        .where(Album.id == album_id)
        .options(selectinload(Album.user), selectinload(Album.images))
    )
    result = await db.execute(query)
    album = result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    # 统计各状态图片数量
    approved_count = 0
    pending_count = 0
    rejected_count = 0
    
    image_responses = []
    for img in sorted(album.images, key=lambda x: x.created_at, reverse=True):
        if img.status == ImageStatus.APPROVED:
            approved_count += 1
        elif img.status == ImageStatus.PENDING:
            pending_count += 1
        elif img.status == ImageStatus.REJECTED:
            rejected_count += 1
        
        image_responses.append(AdminGalleryImageResponse(
            id=img.id,
            filename=img.filename,
            url=img.url,
            width=img.width,
            height=img.height,
            status=img.status.value if img.status else "unknown",
            created_at=img.created_at,
        ))
    
    return AdminGalleryAlbumDetailResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        is_public=album.is_public,
        owner_id=album.user_id,
        owner_name=album.user.username if album.user else "Unknown",
        owner_email=album.user.email if album.user else "",
        images=image_responses,
        total_images=len(album.images),
        approved_count=approved_count,
        pending_count=pending_count,
        rejected_count=rejected_count,
        created_at=album.created_at,
        updated_at=album.updated_at,
    )


@router.put("/{album_id}/toggle-public", response_model=AdminGalleryAlbumResponse)
async def toggle_album_public(
    album_id: int,
    data: AlbumPublicToggle,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员切换相册公开状态"""
    query = (
        select(Album)
        .where(Album.id == album_id)
        .options(selectinload(Album.user), selectinload(Album.images))
    )
    result = await db.execute(query)
    album = result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    album.is_public = data.is_public
    await db.commit()
    await db.refresh(album)
    
    approved_count = sum(
        1 for img in album.images 
        if img.status == ImageStatus.APPROVED
    )
    
    return AdminGalleryAlbumResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        is_public=album.is_public,
        image_count=len(album.images),
        approved_count=approved_count,
        owner_id=album.user_id,
        owner_name=album.user.username if album.user else "Unknown",
        owner_email=album.user.email if album.user else "",
        created_at=album.created_at,
        updated_at=album.updated_at,
    )
