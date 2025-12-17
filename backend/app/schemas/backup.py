"""
Pydantic schemas for backup API.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class BackupProtocol(str, Enum):
    FTP = "ftp"
    SFTP = "sftp"
    S3 = "s3"
    WEBDAV = "webdav"


class SyncStrategy(str, Enum):
    REALTIME = "realtime"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


# Protocol-specific configuration schemas
class FTPConfig(BaseModel):
    """FTP connection configuration."""
    host: str = Field(..., description="FTP server hostname")
    port: int = Field(default=21, ge=1, le=65535)
    username: str = Field(..., description="FTP username")
    password: str = Field(..., description="FTP password")
    remote_path: str = Field(default="/", description="Remote base path")
    passive_mode: bool = Field(default=True, description="Use passive mode")


class SFTPConfig(BaseModel):
    """SFTP connection configuration."""
    host: str = Field(..., description="SFTP server hostname")
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(..., description="SFTP username")
    password: Optional[str] = Field(default=None, description="SFTP password")
    private_key: Optional[str] = Field(default=None, description="SSH private key content")
    remote_path: str = Field(default="/", description="Remote base path")
    
    @field_validator("password", "private_key")
    @classmethod
    def validate_auth(cls, v, info):
        # At least one auth method must be provided
        return v


class S3Config(BaseModel):
    """S3-compatible storage configuration."""
    endpoint: str = Field(..., description="S3 endpoint URL")
    access_key: str = Field(..., description="Access key ID")
    secret_key: str = Field(..., description="Secret access key")
    bucket_name: str = Field(..., description="Bucket name")
    region: Optional[str] = Field(default=None, description="AWS region")
    prefix: str = Field(default="", description="Key prefix for all objects")


class WebDAVConfig(BaseModel):
    """WebDAV connection configuration."""
    url: str = Field(..., description="WebDAV server URL")
    username: str = Field(..., description="WebDAV username")
    password: str = Field(..., description="WebDAV password")
    remote_path: str = Field(default="/", description="Remote base path")


# Request schemas
class BackupNodeCreate(BaseModel):
    """Schema for creating a backup node."""
    name: str = Field(..., max_length=100, description="Node display name")
    protocol: BackupProtocol
    connection_config: Dict[str, Any] = Field(..., description="Protocol-specific configuration")
    sync_strategy: SyncStrategy = Field(default=SyncStrategy.MANUAL)
    schedule_cron: Optional[str] = Field(default=None, description="Cron expression for scheduled sync")
    file_types: str = Field(default="original", description="File types to backup: original, thumbnail, both")
    max_bandwidth: Optional[int] = Field(default=None, ge=0, description="Max bandwidth in KB/s")
    max_concurrent: int = Field(default=3, ge=1, le=10, description="Max concurrent transfers")
    is_enabled: bool = Field(default=True)


class BackupNodeUpdate(BaseModel):
    """Schema for updating a backup node."""
    name: Optional[str] = Field(default=None, max_length=100)
    connection_config: Optional[Dict[str, Any]] = None
    sync_strategy: Optional[SyncStrategy] = None
    schedule_cron: Optional[str] = None
    file_types: Optional[str] = None
    max_bandwidth: Optional[int] = Field(default=None, ge=0)
    max_concurrent: Optional[int] = Field(default=None, ge=1, le=10)
    is_enabled: Optional[bool] = None


# Response schemas
class BackupNodeResponse(BaseModel):
    """Schema for backup node response."""
    id: int
    name: str
    protocol: BackupProtocol
    is_enabled: bool
    sync_strategy: SyncStrategy
    schedule_cron: Optional[str]
    file_types: str
    max_bandwidth: Optional[int]
    max_concurrent: int
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    total_files: int
    total_bytes: int
    created_at: datetime
    updated_at: datetime
    # connection_config is masked for security
    connection_config_masked: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class BackupNodeListResponse(BaseModel):
    """Schema for list of backup nodes."""
    nodes: List[BackupNodeResponse]
    total: int


class BackupLogResponse(BaseModel):
    """Schema for backup log response."""
    id: int
    node_id: int
    node_name: Optional[str] = None
    task_type: str
    status: str
    files_total: int
    files_success: int
    files_failed: int
    bytes_transferred: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    error_details: Optional[str]
    triggered_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class BackupLogListResponse(BaseModel):
    """Schema for list of backup logs."""
    logs: List[BackupLogResponse]
    total: int


class BackupDashboardResponse(BaseModel):
    """Schema for backup dashboard data."""
    total_nodes: int
    enabled_nodes: int
    total_files_backed_up: int
    total_bytes_backed_up: int
    last_backup_at: Optional[datetime]
    nodes_status: List[Dict[str, Any]]
    recent_logs: List[BackupLogResponse]


class ConnectionTestResponse(BaseModel):
    """Schema for connection test result."""
    success: bool
    message: str
    latency_ms: Optional[float]
    details: Dict[str, Any] = {}


class BackupTriggerRequest(BaseModel):
    """Schema for triggering backup operation."""
    image_ids: Optional[List[int]] = Field(default=None, description="Specific image IDs to backup")


class RestoreRequest(BaseModel):
    """Schema for restore operation."""
    image_ids: Optional[List[int]] = Field(default=None, description="Specific image IDs to restore")
    overwrite: bool = Field(default=False, description="Overwrite existing local files")


class BackupTaskResponse(BaseModel):
    """Schema for backup task status."""
    task_id: str
    node_id: int
    task_type: str
    status: str
    progress: float = 0.0
    files_total: int = 0
    files_completed: int = 0
    message: Optional[str] = None


class FileBackupStatusResponse(BaseModel):
    """Schema for file backup status."""
    id: int
    node_id: int
    image_id: int
    remote_path: str
    file_size: int
    checksum: Optional[str]
    status: str
    last_sync_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int

    class Config:
        from_attributes = True


class BackupLogFilter(BaseModel):
    """Schema for filtering backup logs."""
    node_id: Optional[int] = None
    task_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
