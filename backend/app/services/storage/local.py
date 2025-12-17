import os
import aiofiles
from typing import Optional
from app.services.storage.base import StorageBackend
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""
    
    def __init__(self, public_url: Optional[str] = None):
        """
        Initialize local storage.
        
        Args:
            public_url: Optional custom public URL (CDN domain) for accessing files.
                       If provided, URLs will be generated as {public_url}/uploads/{file_path}
                       If not provided, URLs will be /uploads/{file_path} (relative)
        """
        self.upload_path = settings.upload_path
        self.public_url = public_url.rstrip('/') if public_url and public_url.strip() else None
        os.makedirs(self.upload_path, exist_ok=True)
        
        if self.public_url:
            logger.info(f"LocalStorage initialized with custom public_url: {self.public_url}")
    
    async def save(self, content: bytes, filename: str, date_path: Optional[str] = None) -> str:
        """
        Save file to local filesystem.
        
        Args:
            content: File content as bytes
            filename: The filename with extension (e.g., "abc123.png")
            date_path: Optional date path prefix (e.g., "2025/12/14")
        
        Returns:
            The relative file path for database storage (e.g., "2025/12/14/abc123.png")
        
        Raises:
            ValueError: If path contains invalid characters (security check)
        """
        # Security check: prevent path traversal
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            raise ValueError(f"Invalid filename: {filename}")
        if date_path and ('..' in date_path or date_path.startswith('/') or date_path.startswith('\\')):
            raise ValueError(f"Invalid date_path: {date_path}")
        
        if date_path:
            # Create date-based folder structure
            folder_path = os.path.join(self.upload_path, date_path)
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, filename)
            relative_path = f"{date_path}/{filename}"
        else:
            # Legacy: flat structure for backward compatibility
            file_path = os.path.join(self.upload_path, filename)
            relative_path = filename
        
        # Additional security: verify final path is within upload_path
        normalized_path = os.path.normpath(file_path)
        normalized_upload = os.path.normpath(self.upload_path)
        if not normalized_path.startswith(normalized_upload):
            raise ValueError(f"Path escape attempt: {file_path}")
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            logger.info(f"Saved file to: {file_path}")
            return relative_path
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise
    
    async def delete(self, file_path: str) -> bool:
        """
        Delete file from local filesystem.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        
        Returns:
            True if file was deleted, False otherwise
        """
        # Security check: prevent path traversal
        if '..' in file_path or file_path.startswith('/') or file_path.startswith('\\'):
            logger.warning(f"Invalid file_path for deletion: {file_path}")
            return False
        
        full_path = os.path.join(self.upload_path, file_path)
        
        # Additional security: verify final path is within upload_path
        normalized_path = os.path.normpath(full_path)
        normalized_upload = os.path.normpath(self.upload_path)
        if not normalized_path.startswith(normalized_upload):
            logger.warning(f"Path escape attempt in delete: {file_path}")
            return False
        
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Deleted file: {full_path}")
                return True
            logger.warning(f"File not found for deletion: {full_path}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    async def exists(self, file_path: str) -> bool:
        """
        Check if file exists in local filesystem.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        
        Returns:
            True if file exists, False otherwise
        """
        # Security check: prevent path traversal
        if '..' in file_path or file_path.startswith('/') or file_path.startswith('\\'):
            return False
        
        full_path = os.path.join(self.upload_path, file_path)
        
        # Additional security: verify final path is within upload_path
        normalized_path = os.path.normpath(full_path)
        normalized_upload = os.path.normpath(self.upload_path)
        if not normalized_path.startswith(normalized_upload):
            return False
        
        return os.path.exists(full_path)
    
    def get_url(self, file_path: str) -> str:
        """
        Get the URL for a file.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        
        Returns:
            If public_url is set: {public_url}/uploads/{file_path}
            Otherwise: /uploads/{file_path} (relative URL)
        """
        if self.public_url:
            return f"{self.public_url}/uploads/{file_path}"
        return f"/uploads/{file_path}"
    
    @property
    def storage_type(self) -> str:
        return "local"
