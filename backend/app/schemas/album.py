from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class AlbumCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 1 or len(v) > 100:
            raise ValueError("Album name must be between 1 and 100 characters")
        return v.strip()


class AlbumUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 1 or len(v) > 100:
            raise ValueError("Album name must be between 1 and 100 characters")
        return v.strip()


class AlbumResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_public: bool
    image_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlbumListResponse(BaseModel):
    items: List[AlbumResponse]
    total: int
