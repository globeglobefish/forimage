from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional
import os
from app.database import get_db
from app.models.user import User
from app.models.image import Image, ImageStatus
from app.schemas.image import ImageResponse, ImageListResponse, ImageMoveRequest, ImageBatchMoveRequest, ImageUpdateRequest
from app.api.deps import get_current_user
from app.services.storage import get_storage_backend
from app.utils.sanitizer import validate_and_sanitize_title
from app.config import get_settings
from app.api.admin.audit import create_audit_log

router = APIRouter(prefix="/images", tags=["Images"])
config = get_settings()


# IMPORTANT: Batch routes must be defined BEFORE /{image_id} routes
# to prevent FastAPI from treating "batch" as an image_id parameter

@router.put("/batch/move")
async def batch_move_images(
    data: ImageBatchMoveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch move images to a different album."""
    if not data.image_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要移动的图片"
        )
    
    # Verify album belongs to user if album_id is provided
    if data.album_id is not None:
        from app.models.album import Album
        album_result = await db.execute(
            select(Album).where(Album.id == data.album_id, Album.user_id == user.id)
        )
        if not album_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="相册不存在"
            )
    
    # Get user's images
    result = await db.execute(
        select(Image).where(Image.id.in_(data.image_ids), Image.user_id == user.id)
    )
    images = result.scalars().all()
    
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到图片"
        )
    
    # Update album_id for all images
    for image in images:
        image.album_id = data.album_id
    
    await db.commit()
    
    return {"success": True, "count": len(images)}


@router.get("", response_model=ImageListResponse)
async def get_my_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    album_id: Optional[int] = Query(None, description="相册ID，0表示未分类，null表示全部"),
    # Advanced search filters
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    min_width: Optional[int] = Query(None, ge=1, description="最小宽度"),
    max_width: Optional[int] = Query(None, ge=1, description="最大宽度"),
    min_height: Optional[int] = Query(None, ge=1, description="最小高度"),
    max_height: Optional[int] = Query(None, ge=1, description="最大高度"),
    sort_by: str = Query("created_at", description="排序字段: created_at, file_size"),
    sort_order: str = Query("desc", description="排序方向: asc, desc"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's images with advanced search filters."""
    from datetime import datetime
    
    query = select(Image).where(Image.user_id == user.id)
    
    # Album filter
    if album_id is not None:
        if album_id == 0:
            query = query.where(Image.album_id.is_(None))
        else:
            query = query.where(Image.album_id == album_id)
    
    # Date range filter
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.where(Image.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d")
            # Include the entire end day
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.where(Image.created_at <= to_date)
        except ValueError:
            pass
    
    # Dimension filters
    if min_width:
        query = query.where(Image.width >= min_width)
    if max_width:
        query = query.where(Image.width <= max_width)
    if min_height:
        query = query.where(Image.height >= min_height)
    if max_height:
        query = query.where(Image.height <= max_height)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # Sorting
    sort_column = Image.created_at
    if sort_by == "file_size":
        sort_column = Image.file_size
    
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    images = result.scalars().all()
    
    return ImageListResponse(
        items=[ImageResponse.model_validate(img) for img in images],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get image details."""
    result = await db.execute(
        select(Image).where(Image.id == image_id, Image.user_id == user.id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return ImageResponse.model_validate(image)


@router.put("/{image_id}", response_model=ImageResponse)
async def update_image(
    image_id: int,
    data: ImageUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update image information (title, etc.)."""
    result = await db.execute(
        select(Image).where(Image.id == image_id, Image.user_id == user.id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    # 更新标题（带XSS防护）
    if data.title is not None:
        # 空字符串表示清除标题
        if data.title.strip() == '':
            image.title = None
        else:
            sanitized_title = validate_and_sanitize_title(data.title)
            if sanitized_title is None and data.title.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="标题包含无效字符"
                )
            image.title = sanitized_title
    
    await db.commit()
    await db.refresh(image)
    
    return ImageResponse.model_validate(image)


@router.put("/{image_id}/move", response_model=ImageResponse)
async def move_image(
    image_id: int,
    data: ImageMoveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Move image to a different album."""
    result = await db.execute(
        select(Image).where(Image.id == image_id, Image.user_id == user.id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    # Verify album belongs to user if album_id is provided
    if data.album_id is not None:
        from app.models.album import Album
        album_result = await db.execute(
            select(Album).where(Album.id == data.album_id, Album.user_id == user.id)
        )
        if not album_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="相册不存在"
            )
    
    image.album_id = data.album_id
    await db.commit()
    await db.refresh(image)
    
    return ImageResponse.model_validate(image)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an image."""
    result = await db.execute(
        select(Image).where(Image.id == image_id, Image.user_id == user.id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Use file_path for date-based folder structure (e.g., "2025/12/14/abc123.png")
    # Fall back to full_filename for legacy flat structure
    file_path = image.file_path if image.file_path else image.full_filename
    
    # Delete from storage
    storage = get_storage_backend()
    await storage.delete(file_path)
    
    # Delete from database
    await db.delete(image)
    await db.commit()
    
    # 记录审计日志
    from app.utils.rate_limit import get_real_ip
    ip = get_real_ip(request)
    await create_audit_log(
        db=db,
        action="delete",
        ip_address=ip,
        user_id=user.id,
        resource_type="image",
        resource_id=image_id,
        user_agent=request.headers.get("User-Agent"),
        details=f"Deleted image: {file_path}",
        log_status="success"
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_multiple_images(
    image_ids: list[int] = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple images."""
    result = await db.execute(
        select(Image).where(Image.id.in_(image_ids), Image.user_id == user.id)
    )
    images = result.scalars().all()
    
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No images found"
        )
    
    # Delete from storage - use file_path for date-based paths
    storage = get_storage_backend()
    for image in images:
        file_path = image.file_path if image.file_path else image.full_filename
        await storage.delete(file_path)
    
    # Delete from database
    await db.execute(
        delete(Image).where(Image.id.in_([img.id for img in images]))
    )
    await db.commit()
