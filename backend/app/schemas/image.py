from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.image import ImageStatus


class ImageCreate(BaseModel):
    album_id: Optional[int] = None


class ImageResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    title: Optional[str] = None
    extension: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    url: str
    status: ImageStatus
    view_count: int
    album_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    items: List[ImageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ImageUploadResponse(BaseModel):
    success: bool
    image: Optional[ImageResponse] = None
    url: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    bbcode: Optional[str] = None
    error: Optional[str] = None


class ImageMoveRequest(BaseModel):
    album_id: Optional[int] = None  # None to remove from album


class ImageBatchMoveRequest(BaseModel):
    image_ids: List[int]
    album_id: Optional[int] = None  # None to remove from album


class ImageUpdateRequest(BaseModel):
    title: Optional[str] = None  # 图片标题，最长200字符


class ImageSearchParams(BaseModel):
    """Advanced search parameters for filtering images."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None
    sort_by: str = "created_at"  # created_at, file_size
    sort_order: str = "desc"  # asc, desc
