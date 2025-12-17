import oss2
from typing import Optional
from app.services.storage.base import StorageBackend
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class OSSStorage(StorageBackend):
    """Aliyun OSS storage backend."""
    
    def __init__(
        self,
        access_key_id: str = None,
        access_key_secret: str = None,
        bucket_name: str = None,
        endpoint: str = None
    ):
        # Use passed parameters or fall back to settings
        ak_id = access_key_id or settings.oss_access_key_id
        ak_secret = access_key_secret or settings.oss_access_key_secret
        bucket = bucket_name or settings.oss_bucket_name
        ep = endpoint or settings.oss_endpoint
        
        if not all([ak_id, ak_secret, bucket, ep]):
            raise ValueError("OSS configuration is incomplete")
        
        self.auth = oss2.Auth(ak_id, ak_secret)
        self.bucket = oss2.Bucket(self.auth, ep, bucket)
        self.endpoint = ep
        self.bucket_name = bucket
    
    async def save(self, content: bytes, filename: str, date_path: Optional[str] = None) -> str:
        """
        Save file to Aliyun OSS.
        
        Args:
            content: File content as bytes
            filename: The filename with extension (e.g., "abc123.png")
            date_path: Optional date path prefix (e.g., "2025/12/14")
        
        Returns:
            The relative file path for database storage
        
        Raises:
            ValueError: If path contains invalid characters (security check)
        """
        # Security check: prevent path traversal
        if '..' in filename or filename.startswith('/'):
            raise ValueError(f"Invalid filename: {filename}")
        if date_path and ('..' in date_path or date_path.startswith('/')):
            raise ValueError(f"Invalid date_path: {date_path}")
        
        try:
            if date_path:
                key = f"images/{date_path}/{filename}"
                relative_path = f"{date_path}/{filename}"
            else:
                key = f"images/{filename}"
                relative_path = filename
            
            self.bucket.put_object(key, content)
            logger.info(f"Saved file to OSS: {key}")
            return relative_path
        except Exception as e:
            logger.error(f"Error saving file to OSS {filename}: {e}")
            raise
    
    async def delete(self, file_path: str) -> bool:
        """
        Delete file from Aliyun OSS.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        """
        try:
            key = f"images/{file_path}"
            self.bucket.delete_object(key)
            logger.info(f"Deleted file from OSS: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from OSS {file_path}: {e}")
            return False
    
    async def exists(self, file_path: str) -> bool:
        """
        Check if file exists in Aliyun OSS.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        """
        try:
            key = f"images/{file_path}"
            return self.bucket.object_exists(key)
        except:
            return False
    
    def get_url(self, file_path: str) -> str:
        """
        Get the public URL for a file in OSS.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        """
        # Extract domain from endpoint
        endpoint = self.endpoint.replace("https://", "").replace("http://", "")
        return f"https://{self.bucket_name}.{endpoint}/images/{file_path}"
    
    @property
    def storage_type(self) -> str:
        return "oss"
