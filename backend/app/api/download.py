"""
Download API endpoints for batch downloading images.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user, get_current_user_optional
from app.services.download import DownloadService
from app.utils.rate_limit import get_real_ip, check_rate_limit

router = APIRouter(prefix="/download", tags=["Download"])


class BatchDownloadRequest(BaseModel):
    image_ids: List[int]


@router.post("/batch")
async def batch_download(
    request: Request,
    data: BatchDownloadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download multiple images as a ZIP file.
    Only downloads images owned by the current user.
    """
    if not data.image_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No images selected"
        )
    
    if len(data.image_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 images per download"
        )
    
    service = DownloadService(db)
    images = await service.get_images_by_ids(data.image_ids, user_id=user.id)
    
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No images found or you don't have permission to download them"
        )
    
    # Generate ZIP
    zip_buffer = await service.create_zip_stream(images)
    filename = service.generate_zip_filename()
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(zip_buffer.getbuffer().nbytes),
        }
    )


@router.get("/album/{album_id}")
async def download_album(
    album_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download all images from an album as a ZIP file.
    Only works for albums owned by the current user.
    """
    service = DownloadService(db)
    album, images = await service.get_album_images(album_id, user_id=user.id)
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found or you don't have permission"
        )
    
    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Album is empty"
        )
    
    # Generate ZIP
    zip_buffer = await service.create_zip_stream(images)
    filename = service.generate_album_zip_filename(album.name)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(zip_buffer.getbuffer().nbytes),
        }
    )
