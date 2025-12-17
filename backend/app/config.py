from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "44img"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "dev-secret-key-change-in-production"
    app_url: str = "http://localhost:3000"

    # Database (MySQL)
    database_url: str = "mysql+aiomysql://imgbed:your_password@localhost:3306/imgbed"

    # Redis (optional in development)
    redis_url: Optional[str] = None
    redis_enabled: bool = False

    # JWT
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # SMTP (DEPRECATED - now configured in database via admin panel)
    # These settings are kept for backward compatibility but are no longer used
    # Please configure email settings in Admin Panel -> System Settings -> Email Settings
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: str = "Forimage"
    smtp_enabled: bool = False

    # Upload
    upload_max_size_guest: int = 5242880  # 5MB
    upload_max_size_user: int = 10485760  # 10MB
    upload_allowed_extensions: str = "png,jpg,jpeg,gif,webp"
    upload_path: str = "./uploads"
    image_compression_quality: int = 85

    # Rate Limiting
    rate_limit_guest_uploads: str = "10/hour"
    rate_limit_user_uploads: str = "100/hour"
    rate_limit_login_attempts: str = "5/minute"

    # Storage
    storage_type: str = "local"  # local, s3c, oss, cos

    # S3 Compatible Storage (unified)
    s3c_access_key_id: Optional[str] = None
    s3c_secret_access_key: Optional[str] = None
    s3c_bucket_name: Optional[str] = None
    s3c_endpoint_url: Optional[str] = None
    s3c_region: Optional[str] = None
    s3c_public_url: Optional[str] = None

    # Aliyun OSS (native SDK)
    oss_access_key_id: Optional[str] = None
    oss_access_key_secret: Optional[str] = None
    oss_bucket_name: Optional[str] = None
    oss_endpoint: Optional[str] = None

    # Tencent Cloud COS (native SDK)
    cos_secret_id: Optional[str] = None
    cos_secret_key: Optional[str] = None
    cos_bucket_name: Optional[str] = None
    cos_region: Optional[str] = None
    cos_public_url: Optional[str] = None

    # Legacy support (for backward compatibility)
    r2_access_key_id: Optional[str] = None
    r2_secret_access_key: Optional[str] = None
    r2_bucket_name: Optional[str] = None
    r2_endpoint: Optional[str] = None
    r2_public_url: Optional[str] = None
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[str] = None
    s3_bucket_name: Optional[str] = None
    s3_region: Optional[str] = None

    # Audit
    audit_enabled: bool = False
    audit_provider: Optional[str] = None
    audit_api_key: Optional[str] = None
    audit_api_secret: Optional[str] = None

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.upload_allowed_extensions.split(",")]

    class Config:
        env_file = "../.env"  # .env file is in project root
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
