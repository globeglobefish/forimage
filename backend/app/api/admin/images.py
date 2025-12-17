from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.image import Image, ImageStatus
from app.api.deps import get_admin_user
from app.services.storage import get_storage_backend
from app.api.admin.audit import create_audit_log
from app.utils.rate_limit import get_real_ip

router = APIRouter(prefix="/images")


class AdminImageResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    title: Optional[str] = None
    extension: str
    mime_type: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    url: str
    status: ImageStatus
    view_count: int
    user_id: Optional[int]
    guest_ip: Optional[str]
    upload_ip: Optional[str]  # 所有上传者的IP
    storage_type: str
    created_at: datetime
    
    # User info
    username: Optional[str] = None

    class Config:
        from_attributes = True


class AdminImageListResponse(BaseModel):
    items: List[AdminImageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ImageStatusUpdate(BaseModel):
    status: ImageStatus


@router.get("", response_model=AdminImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ImageStatus] = Query(None, alias="status"),
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all images with filtering."""
    query = select(Image, User.username).outerjoin(User, Image.user_id == User.id)
    
    if status_filter:
        query = query.where(Image.status == status_filter)
    
    if user_id:
        query = query.where(Image.user_id == user_id)
    
    if search:
        query = query.where(
            Image.filename.ilike(f"%{search}%") | 
            Image.original_filename.ilike(f"%{search}%")
        )
    
    # Count total
    count_query = select(func.count()).select_from(Image)
    if status_filter:
        count_query = count_query.where(Image.status == status_filter)
    if user_id:
        count_query = count_query.where(Image.user_id == user_id)
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    query = query.order_by(Image.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    rows = result.all()
    
    items = []
    for image, username in rows:
        item = AdminImageResponse.model_validate(image)
        item.username = username
        items.append(item)
    
    return AdminImageListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/pending", response_model=AdminImageListResponse)
async def list_pending_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List images pending review."""
    return await list_images(
        page=page,
        page_size=page_size,
        status_filter=ImageStatus.PENDING,
        user_id=None,
        search=None,
        admin=admin,
        db=db,
    )


@router.get("/{image_id}", response_model=AdminImageResponse)
async def get_image(
    image_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get image details."""
    result = await db.execute(
        select(Image, User.username)
        .outerjoin(User, Image.user_id == User.id)
        .where(Image.id == image_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    image, username = row
    response = AdminImageResponse.model_validate(image)
    response.username = username
    
    return response


@router.put("/{image_id}/status", response_model=AdminImageResponse)
async def update_image_status(
    image_id: int,
    data: ImageStatusUpdate,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update image status (approve/reject)."""
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    old_status = image.status
    image.status = data.status
    await db.commit()
    await db.refresh(image)
    
    # 记录审计日志
    ip = get_real_ip(request)
    await create_audit_log(
        db=db,
        action="admin_update_status",
        ip_address=ip,
        user_id=admin.id,
        resource_type="image",
        resource_id=image_id,
        user_agent=request.headers.get("User-Agent"),
        details=f"Admin changed image status: {old_status.value} -> {data.status.value}",
        log_status="success"
    )
    
    return AdminImageResponse.model_validate(image)


@router.post("/batch-approve")
async def batch_approve_images(
    image_ids: List[int],
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve multiple images."""
    result = await db.execute(select(Image).where(Image.id.in_(image_ids)))
    images = result.scalars().all()
    
    for image in images:
        image.status = ImageStatus.APPROVED
    
    await db.commit()
    
    return {"message": f"Approved {len(images)} images"}


@router.post("/batch-reject")
async def batch_reject_images(
    image_ids: List[int],
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject multiple images."""
    result = await db.execute(select(Image).where(Image.id.in_(image_ids)))
    images = result.scalars().all()
    
    for image in images:
        image.status = ImageStatus.REJECTED
    
    await db.commit()
    
    return {"message": f"Rejected {len(images)} images"}


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an image."""
    result = await db.execute(select(Image).where(Image.id == image_id))
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
    ip = get_real_ip(request)
    await create_audit_log(
        db=db,
        action="admin_delete",
        ip_address=ip,
        user_id=admin.id,
        resource_type="image",
        resource_id=image_id,
        user_agent=request.headers.get("User-Agent"),
        details=f"Admin deleted image: {file_path}",
        log_status="success"
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def batch_delete_images(
    image_ids: List[int] = Query(...),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple images."""
    result = await db.execute(select(Image).where(Image.id.in_(image_ids)))
    images = result.scalars().all()
    
    # Delete from storage - use file_path for date-based paths
    storage = get_storage_backend()
    for image in images:
        file_path = image.file_path if image.file_path else image.full_filename
        await storage.delete(file_path)
    
    # Delete from database
    await db.execute(delete(Image).where(Image.id.in_([img.id for img in images])))
    await db.commit()
