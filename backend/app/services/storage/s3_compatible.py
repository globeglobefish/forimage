"""
Unified S3-Compatible Storage Backend

Supports all S3-compatible object storage services:
- AWS S3
- Cloudflare R2
- Tencent Cloud COS (S3 mode)
- MinIO
- Backblaze B2
- DigitalOcean Spaces
- Any other S3-compatible service

Configuration is done via:
- endpoint_url: Custom endpoint (required for non-AWS services)
- region: Region name (use 'auto' for R2, specific region for others)
- access_key_id: Access key
- secret_access_key: Secret key
- bucket_name: Bucket name
- public_url: Optional custom public URL for accessing files
- path_style: Use path-style addressing (default: auto-detect)
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional
from app.services.storage.base import StorageBackend
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


# Preset configurations for common providers
S3_PRESETS = {
    'aws': {
        'name': 'AWS S3',
        'endpoint_pattern': None,  # Uses default AWS endpoint
        'region_required': True,
        'path_style': False,
    },
    'r2': {
        'name': 'Cloudflare R2',
        'endpoint_pattern': 'https://{account_id}.r2.cloudflarestorage.com',
        'region_required': False,
        'default_region': 'auto',
        'path_style': True,
    },
    'cos': {
        'name': 'Tencent Cloud COS',
        'endpoint_pattern': 'https://cos.{region}.myqcloud.com',
        'region_required': True,
        'path_style': False,
    },
    'minio': {
        'name': 'MinIO',
        'endpoint_pattern': None,  # User provides full endpoint
        'region_required': False,
        'default_region': 'us-east-1',
        'path_style': True,
    },
    'b2': {
        'name': 'Backblaze B2',
        'endpoint_pattern': 'https://s3.{region}.backblazeb2.com',
        'region_required': True,
        'path_style': False,
    },
    'spaces': {
        'name': 'DigitalOcean Spaces',
        'endpoint_pattern': 'https://{region}.digitaloceanspaces.com',
        'region_required': True,
        'path_style': False,
    },
}


class S3CompatibleStorage(StorageBackend):
    """Unified S3-compatible storage backend."""
    
    def __init__(
        self,
        access_key_id: str = None,
        secret_access_key: str = None,
        bucket_name: str = None,
        endpoint_url: str = None,
        region: str = None,
        public_url: str = None,
        path_style: bool = None,
        provider: str = None,
    ):
        """
        Initialize S3-compatible storage.
        
        Args:
            access_key_id: Access Key ID
            secret_access_key: Secret Access Key
            bucket_name: Bucket name
            endpoint_url: Custom endpoint URL (required for non-AWS services)
            region: Region name (use 'auto' for R2)
            public_url: Custom public URL for accessing files
            path_style: Use path-style addressing (auto-detect if None)
            provider: Provider preset name (aws, r2, cos, minio, b2, spaces, custom)
        """
        self.provider = provider or 'custom'
        
        # Get values from parameters or settings
        ak_id = access_key_id or getattr(settings, 's3c_access_key_id', None)
        ak_secret = secret_access_key or getattr(settings, 's3c_secret_access_key', None)
        bucket = bucket_name or getattr(settings, 's3c_bucket_name', None)
        endpoint = endpoint_url or getattr(settings, 's3c_endpoint_url', None)
        reg = region or getattr(settings, 's3c_region', None) or 'us-east-1'
        pub_url = public_url or getattr(settings, 's3c_public_url', None)
        
        if not all([ak_id, ak_secret, bucket]):
            raise ValueError("S3-compatible storage configuration is incomplete (need access_key_id, secret_access_key, bucket_name)")
        
        # Determine path style
        if path_style is None:
            # Auto-detect based on provider or endpoint
            if self.provider in ['r2', 'minio']:
                path_style = True
            elif endpoint and any(x in endpoint for x in ['r2.cloudflarestorage', 'minio', ':9000']):
                path_style = True
            else:
                path_style = False
        
        # Build boto3 config
        config_kwargs = {
            'signature_version': 's3v4',
        }
        if path_style:
            config_kwargs['s3'] = {'addressing_style': 'path'}
        
        # Build client kwargs
        client_kwargs = {
            'aws_access_key_id': ak_id,
            'aws_secret_access_key': ak_secret,
            'region_name': reg,
            'config': Config(**config_kwargs),
        }
        
        if endpoint:
            client_kwargs['endpoint_url'] = endpoint
        
        self.client = boto3.client('s3', **client_kwargs)
        self.bucket = bucket
        self.region = reg
        self.endpoint = endpoint.rstrip('/') if endpoint else None
        self.public_url = pub_url.rstrip('/') if pub_url else None
        self._path_style = path_style
        
        logger.info(f"S3CompatibleStorage initialized: provider={self.provider}, bucket={self.bucket}, "
                    f"endpoint={self.endpoint}, public_url={self.public_url}, path_style={self._path_style}")
    
    async def save(self, content: bytes, filename: str, date_path: Optional[str] = None) -> str:
        """
        Save file to S3-compatible storage.
        
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
            
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
            logger.info(f"Saved file to S3-compatible storage ({self.provider}): {key}")
            return relative_path
        except Exception as e:
            logger.error(f"Error saving file to S3-compatible storage {filename}: {e}")
            raise
    
    async def delete(self, file_path: str) -> bool:
        """
        Delete file from S3-compatible storage.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        """
        try:
            key = f"images/{file_path}"
            self.client.delete_object(
                Bucket=self.bucket,
                Key=key,
            )
            logger.info(f"Deleted file from S3-compatible storage: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from S3-compatible storage {file_path}: {e}")
            return False
    
    async def exists(self, file_path: str) -> bool:
        """
        Check if file exists in S3-compatible storage.
        
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
        except ClientError:
            return False
    
    def get_url(self, file_path: str) -> str:
        """
        Get the public URL for a file.
        
        Args:
            file_path: Relative file path (e.g., "2025/12/14/abc123.png" or "abc123.png")
        
        Returns:
            Public URL for the file
        """
        key = f"images/{file_path}"
        
        # Use custom public URL if provided
        if self.public_url:
            url = f"{self.public_url}/{key}"
            logger.debug(f"get_url using public_url: {url}")
            return url
        
        # Build URL based on endpoint and path style
        if self.endpoint:
            if self._path_style:
                url = f"{self.endpoint}/{self.bucket}/{key}"
            else:
                # Virtual-hosted style - need to insert bucket into hostname
                # e.g., https://bucket.cos.ap-guangzhou.myqcloud.com/key
                from urllib.parse import urlparse
                parsed = urlparse(self.endpoint)
                url = f"{parsed.scheme}://{self.bucket}.{parsed.netloc}/{key}"
            logger.debug(f"get_url using endpoint (path_style={self._path_style}): {url}")
            return url
        else:
            # Default AWS S3 URL
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            logger.debug(f"get_url using default AWS URL: {url}")
            return url
    
    @property
    def storage_type(self) -> str:
        return "s3c"  # s3-compatible
