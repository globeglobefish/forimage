"""
Public Gallery API - 公开画廊接口
允许访问公开相册和其中的图片，无需登录
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.album import Album
from app.models.image import Image, ImageStatus
from app.models.user import User

router = APIRouter(prefix="/gallery", tags=["Gallery"])


# Response schemas
class GalleryImageResponse(BaseModel):
    """公开图片响应"""
    id: int
    filename: str
    title: Optional[str] = None  # 用户设置的标题
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class GalleryAlbumResponse(BaseModel):
    """公开相册响应"""
    id: int
    name: str
    description: Optional[str] = None
    image_count: int
    cover_image: Optional[GalleryImageResponse] = None
    owner_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class GalleryAlbumDetailResponse(BaseModel):
    """公开相册详情响应"""
    id: int
    name: str
    description: Optional[str] = None
    owner_name: str
    images: List[GalleryImageResponse]
    total_images: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class GalleryListResponse(BaseModel):
    """画廊列表响应"""
    albums: List[GalleryAlbumResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=GalleryListResponse)
async def get_public_albums(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    获取所有公开相册列表
    无需登录即可访问
    """
    offset = (page - 1) * page_size
    
    # 查询公开相册总数
    count_query = select(func.count(Album.id)).where(Album.is_public == True)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 查询公开相册列表
    query = (
        select(Album)
        .where(Album.is_public == True)
        .options(selectinload(Album.user), selectinload(Album.images))
        .order_by(Album.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    albums = result.scalars().all()
    
    # 构建响应
    album_responses = []
    for album in albums:
        # 获取已审核通过的图片
        approved_images = [
            img for img in album.images 
            if img.status == ImageStatus.APPROVED
        ]
        
        # 获取封面图（第一张图片）
        cover_image = None
        if approved_images:
            first_img = approved_images[0]
            cover_image = GalleryImageResponse(
                id=first_img.id,
                filename=first_img.filename,
                url=first_img.url,
                width=first_img.width,
                height=first_img.height,
                created_at=first_img.created_at,
            )
        
        album_responses.append(GalleryAlbumResponse(
            id=album.id,
            name=album.name,
            description=album.description,
            image_count=len(approved_images),
            cover_image=cover_image,
            owner_name=album.user.username if album.user else "Unknown",
            created_at=album.created_at,
        ))
    
    return GalleryListResponse(
        albums=album_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{album_id}", response_model=GalleryAlbumDetailResponse)
async def get_public_album_detail(
    album_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", description="排序字段: created_at, file_size"),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取公开相册详情及其图片
    无需登录即可访问
    """
    # 查询相册
    query = (
        select(Album)
        .where(Album.id == album_id, Album.is_public == True)
        .options(selectinload(Album.user), selectinload(Album.images))
    )
    result = await db.execute(query)
    album = result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found or not public"
        )
    
    # 获取已审核通过的图片
    approved_images = [
        img for img in album.images 
        if img.status == ImageStatus.APPROVED
    ]
    
    # 排序图片
    reverse = sort_order == "desc"
    if sort_by == "file_size":
        approved_images.sort(key=lambda x: x.file_size or 0, reverse=reverse)
    else:  # created_at (default)
        approved_images.sort(key=lambda x: x.created_at, reverse=reverse)
    
    total_images = len(approved_images)
    offset = (page - 1) * page_size
    paginated_images = approved_images[offset:offset + page_size]
    
    image_responses = [
        GalleryImageResponse(
            id=img.id,
            filename=img.filename,
            title=img.title,  # 包含用户设置的标题
            url=img.url,
            width=img.width,
            height=img.height,
            file_size=img.file_size,
            created_at=img.created_at,
        )
        for img in paginated_images
    ]
    
    return GalleryAlbumDetailResponse(
        id=album.id,
        name=album.name,
        description=album.description,
        owner_name=album.user.username if album.user else "Unknown",
        images=image_responses,
        total_images=total_images,
        created_at=album.created_at,
    )


@router.get("/{album_id}/download")
async def download_public_album(
    album_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Download all images from a public album as a ZIP file.
    Rate limited to 5 downloads per hour per IP.
    """
    from app.services.download import DownloadService
    from app.utils.rate_limit import get_real_ip
    from app.redis import get_redis
    
    ip = get_real_ip(request)
    
    # Rate limiting: 5 downloads per hour per IP
    redis = await get_redis()
    if redis:
        rate_key = f"gallery_download:{ip}"
        current = await redis.get(rate_key)
        if current and int(current) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Maximum 5 downloads per hour. Please try again later."
            )
        
        # Increment counter
        pipe = redis.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, 3600)  # 1 hour expiry
        await pipe.execute()
    
    service = DownloadService(db)
    album, images = await service.get_album_images(album_id, public_only=True)
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found or not public"
        )
    
    # Filter to approved images only
    from app.models.image import ImageStatus
    approved_images = [img for img in images if img.status == ImageStatus.APPROVED]
    
    if not approved_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Album is empty"
        )
    
    # Generate ZIP
    zip_buffer = await service.create_zip_stream(approved_images)
    filename = service.generate_album_zip_filename(album.name)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(zip_buffer.getbuffer().nbytes),
        }
    )
