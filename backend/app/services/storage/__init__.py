"""
Storage Backend Factory

Supports:
- local: Local filesystem storage
- s3c: S3-compatible storage (AWS S3, Cloudflare R2, MinIO, Backblaze B2, DigitalOcean Spaces, etc.)
- oss: Aliyun OSS (native SDK)
- cos: Tencent Cloud COS (native SDK, recommended with audit service)
"""
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorage
from app.config import get_settings

settings = get_settings()


async def get_storage_backend_async() -> StorageBackend:
    """Get the configured storage backend from database settings."""
    from app.services.settings import get_storage_type, get_setting
    
    storage_type = (await get_storage_type()).lower()
    
    if storage_type == "s3c":
        # Unified S3-compatible storage
        try:
            from app.services.storage.s3_compatible import S3CompatibleStorage
            s3c_endpoint = await get_setting("storage_s3c_endpoint_url")
            s3c_region = await get_setting("storage_s3c_region")
            s3c_public_url = await get_setting("storage_s3c_public_url")
            return S3CompatibleStorage(
                access_key_id=await get_setting("storage_s3c_access_key_id"),
                secret_access_key=await get_setting("storage_s3c_secret_access_key"),
                bucket_name=await get_setting("storage_s3c_bucket_name"),
                endpoint_url=s3c_endpoint if s3c_endpoint and s3c_endpoint.strip() else None,
                region=s3c_region if s3c_region and s3c_region.strip() else None,
                public_url=s3c_public_url if s3c_public_url and s3c_public_url.strip() else None,
                provider=await get_setting("storage_s3c_provider") or 'custom',
            )
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
    
    elif storage_type == "oss":
        # Aliyun OSS (native SDK)
        try:
            from app.services.storage.oss import OSSStorage
            return OSSStorage(
                access_key_id=await get_setting("storage_oss_access_key_id"),
                access_key_secret=await get_setting("storage_oss_access_key_secret"),
                bucket_name=await get_setting("storage_oss_bucket_name"),
                endpoint=await get_setting("storage_oss_endpoint"),
            )
        except ImportError:
            raise ImportError("oss2 package not installed. Run: pip install oss2")
    
    elif storage_type == "cos":
        # Tencent Cloud COS (native SDK)
        try:
            from app.services.storage.cos import COSStorage
            return COSStorage(
                secret_id=await get_setting("storage_cos_secret_id"),
                secret_key=await get_setting("storage_cos_secret_key"),
                bucket_name=await get_setting("storage_cos_bucket_name"),
                region=await get_setting("storage_cos_region"),
                public_url=await get_setting("storage_cos_public_url") or None,
            )
        except ImportError:
            raise ImportError("cos-python-sdk-v5 package not installed. Run: pip install cos-python-sdk-v5")
    
    # Legacy support for old storage types (r2, s3)
    elif storage_type == "r2":
        # Redirect to S3-compatible with R2 preset
        try:
            from app.services.storage.s3_compatible import S3CompatibleStorage
            r2_public_url = await get_setting("storage_r2_public_url")
            return S3CompatibleStorage(
                access_key_id=await get_setting("storage_r2_access_key_id"),
                secret_access_key=await get_setting("storage_r2_secret_access_key"),
                bucket_name=await get_setting("storage_r2_bucket_name"),
                endpoint_url=await get_setting("storage_r2_endpoint"),
                region='auto',
                public_url=r2_public_url if r2_public_url and r2_public_url.strip() else None,
                provider='r2',
            )
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
    
    elif storage_type == "s3":
        # Redirect to S3-compatible with AWS preset
        try:
            from app.services.storage.s3_compatible import S3CompatibleStorage
            return S3CompatibleStorage(
                access_key_id=await get_setting("storage_s3_access_key_id"),
                secret_access_key=await get_setting("storage_s3_secret_access_key"),
                bucket_name=await get_setting("storage_s3_bucket_name"),
                region=await get_setting("storage_s3_region"),
                provider='aws',
            )
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
    
    else:
        # Local storage with optional custom public URL (CDN)
        local_public_url = await get_setting("storage_local_public_url")
        return LocalStorage(
            public_url=local_public_url if local_public_url and local_public_url.strip() else None
        )


def get_storage_backend() -> StorageBackend:
    """Get the configured storage backend (sync version, uses .env settings)."""
    storage_type = settings.storage_type.lower()
    
    if storage_type == "s3c":
        try:
            from app.services.storage.s3_compatible import S3CompatibleStorage
            return S3CompatibleStorage()
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
    
    elif storage_type == "oss":
        try:
            from app.services.storage.oss import OSSStorage
            return OSSStorage()
        except ImportError:
            raise ImportError("oss2 package not installed. Run: pip install oss2")
    
    elif storage_type == "cos":
        try:
            from app.services.storage.cos import COSStorage
            return COSStorage()
        except ImportError:
            raise ImportError("cos-python-sdk-v5 package not installed. Run: pip install cos-python-sdk-v5")
    
    # Legacy support - redirect to S3CompatibleStorage
    elif storage_type in ("r2", "s3"):
        try:
            from app.services.storage.s3_compatible import S3CompatibleStorage
            return S3CompatibleStorage(provider=storage_type if storage_type == 'r2' else 'aws')
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
    
    else:
        return LocalStorage()


__all__ = [
    "StorageBackend",
    "LocalStorage", 
    "get_storage_backend",
    "get_storage_backend_async",
]
