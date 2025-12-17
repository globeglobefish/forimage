"""
Download service for batch downloading images as ZIP files.
"""
import io
import os
import zipfile
from datetime import datetime
from typing import List, Optional, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.models.album import Album
from app.config import get_settings

settings = get_settings()


class DownloadService:
    """Service for generating ZIP downloads of images."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_images_by_ids(
        self, 
        image_ids: List[int], 
        user_id: Optional[int] = None
    ) -> List[Image]:
        """Get images by IDs, optionally filtered by user ownership."""
        query = select(Image).where(Image.id.in_(image_ids))
        if user_id is not None:
            query = query.where(Image.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_album_images(
        self, 
        album_id: int, 
        user_id: Optional[int] = None,
        public_only: bool = False
    ) -> tuple[Optional[Album], List[Image]]:
        """Get album and its images."""
        # Get album
        album_query = select(Album).where(Album.id == album_id)
        if public_only:
            album_query = album_query.where(Album.is_public == True)
        elif user_id is not None:
            album_query = album_query.where(Album.user_id == user_id)
        
        result = await self.db.execute(album_query)
        album = result.scalar_one_or_none()
        
        if not album:
            return None, []
        
        # Get images
        images_query = select(Image).where(Image.album_id == album_id)
        result = await self.db.execute(images_query)
        images = list(result.scalars().all())
        
        return album, images
    
    def generate_zip_filename(self, prefix: str = "forimage_images") -> str:
        """Generate ZIP filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.zip"
    
    def generate_album_zip_filename(self, album_name: str) -> str:
        """Generate ZIP filename for album download."""
        # Sanitize album name for filename
        safe_name = "".join(c for c in album_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
        if not safe_name:
            safe_name = "album"
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"{safe_name}_{timestamp}.zip"
    
    async def create_zip_stream(self, images: List[Image]) -> io.BytesIO:
        """Create a ZIP file in memory containing the specified images."""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for image in images:
                # Build local file path
                local_path = os.path.join(settings.upload_path, image.file_path)
                
                if os.path.exists(local_path):
                    # Use original filename or generated filename
                    filename = image.original_filename or image.full_filename
                    # Ensure unique filenames in ZIP
                    arcname = self._get_unique_arcname(zip_file, filename)
                    zip_file.write(local_path, arcname)
        
        zip_buffer.seek(0)
        return zip_buffer
    
    def _get_unique_arcname(self, zip_file: zipfile.ZipFile, filename: str) -> str:
        """Get unique filename for ZIP archive to avoid duplicates."""
        existing_names = set(zip_file.namelist())
        if filename not in existing_names:
            return filename
        
        # Add counter suffix for duplicates
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_name = f"{name}_{counter}{ext}"
            if new_name not in existing_names:
                return new_name
            counter += 1
