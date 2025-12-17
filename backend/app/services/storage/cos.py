"""
Tencent Cloud COS Storage Backend (Native SDK)

Uses the official cos-python-sdk-v5 for full feature support.
Recommended when using Tencent Cloud's content moderation (audit) service.

For S3-compatible mode, use S3CompatibleStorage with provider='cos' instead.
"""
from typing import Optional
from app.services.storage.base import StorageBackend
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class COSStorage(StorageBackend):
    """Tencent Cloud COS storage backend using native SDK."""
    
    def __init__(
        self,
        secret_id: str = None,
        secret_key: str = None,
        bucket_name: str = None,
        region: str = None,
        public_url: str = None,
    ):
        """
        Initialize COS storage.
        
        Args:
            secret_id: Tencent Cloud SecretId
            secret_key: Tencent Cloud SecretKey
            bucket_name: COS Bucket name (format: bucket-appid, e.g., mybucket-1250000000)
            region: COS Region (e.g., ap-guangzhou, ap-shanghai)
            public_url: Optional custom domain for accessing files
        """
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise ImportError("cos-python-sdk-v5 package not installed. Run: pip install cos-python-sdk-v5")
        
        sid = secret_id or getattr(settings, 'cos_secret_id', None)
        skey = secret_key or getattr(settings, 'cos_secret_key', None)
        bucket = bucket_name or getattr(settings, 'cos_bucket_name', None)
        reg = region or getattr(settings, 'cos_region', None)
        pub_url = public_url or getattr(settings, 'cos_public_url', None)
        
        if not all([sid, skey, bucket, reg]):
            raise ValueError("COS configuration is incomplete (need secret_id, secret_key, bucket_name, region)")
        
        config = CosConfig(
            Region=reg,
            SecretId=sid,
            SecretKey=skey,
            Scheme='https',
        )
        
        self.client = CosS3Client(config)
        self.bucket = bucket
        self.region = reg
        self.public_url = pub_url.rstrip('/') if pub_url else None
    
    async def save(self, content: bytes, filename: str, date_path: Optional[str] = None) -> str:
        """
        Save file to Tencent Cloud COS.
        
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
            
            # Determine content type
            ext = filename.rsplit('.', 1)[-1].lower()
            content_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
            }
            content_type = content_types.get(ext, 'application/octet-stream')
            
            # Use put_object for bytes content
            from io import BytesIO
            self.client.put_object(
                Bucket=self.bucket,
                Body=BytesIO(content),
                Key=key,
                ContentType=content_type,
            )
            logger.info(f"Saved file to COS: {key}")
            return relative_path
        except Exception as e:
            logger.error(f"Error saving file to COS {filename}: {e}")
            raise
    
    async def delete(self, file_path: str) -> bool:
        """
        Delete file from Tencent Cloud COS.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        """
        try:
            key = f"images/{file_path}"
            self.client.delete_object(
                Bucket=self.bucket,
                Key=key,
            )
            logger.info(f"Deleted file from COS: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from COS {file_path}: {e}")
            return False
    
    async def exists(self, file_path: str) -> bool:
        """
        Check if file exists in Tencent Cloud COS.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        """
        try:
            key = f"images/{file_path}"
            self.client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except Exception:
            return False
    
    def get_url(self, file_path: str) -> str:
        """
        Get the public URL for a file in COS.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        
        Returns:
            Public URL for the file
        """
        key = f"images/{file_path}"
        
        if self.public_url:
            return f"{self.public_url}/{key}"
        else:
            # Default COS URL format
            return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{key}"
    
    @property
    def storage_type(self) -> str:
        return "cos"
