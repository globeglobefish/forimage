"""
Backup models for multi-node backup functionality.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, BigInteger, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class BackupProtocol(str, enum.Enum):
    """Supported backup protocols."""
    FTP = "ftp"
    SFTP = "sftp"
    S3 = "s3"
    WEBDAV = "webdav"


class SyncStrategy(str, enum.Enum):
    """Backup synchronization strategies."""
    REALTIME = "realtime"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class SyncStatus(str, enum.Enum):
    """Status of last sync operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class FileBackupStatus(str, enum.Enum):
    """Status of individual file backup."""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    DELETED = "deleted"


class BackupTaskType(str, enum.Enum):
    """Type of backup task."""
    BACKUP = "backup"
    REALTIME = "realtime"
    RESTORE = "restore"
    SYNC = "sync"
    TEST = "test"


class BackupTaskStatus(str, enum.Enum):
    """Status of backup task."""
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupNode(Base):
    """Backup node configuration model."""
    __tablename__ = "backup_nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="节点名称")
    protocol = Column(
        SQLEnum(BackupProtocol, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Connection settings (encrypted JSON)
    connection_config = Column(Text, nullable=False, comment="加密的连接配置JSON")
    
    # Sync strategy
    sync_strategy = Column(
        SQLEnum(SyncStrategy, values_callable=lambda x: [e.value for e in x]),
        default=SyncStrategy.MANUAL,
        nullable=False
    )
    schedule_cron = Column(String(100), nullable=True, comment="Cron表达式（scheduled模式）")
    file_types = Column(String(50), default="original", comment="original,thumbnail,both")
    
    # Performance limits
    max_bandwidth = Column(Integer, nullable=True, comment="最大带宽(KB/s)，NULL为不限制")
    max_concurrent = Column(Integer, default=3, comment="最大并发数")
    
    # Status
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(
        SQLEnum(SyncStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    total_files = Column(Integer, default=0)
    total_bytes = Column(BigInteger, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    file_statuses = relationship("BackupFileStatus", back_populates="node", cascade="all, delete-orphan")
    logs = relationship("BackupLog", back_populates="node", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BackupNode(id={self.id}, name={self.name}, protocol={self.protocol})>"



class BackupFileStatus(Base):
    """File backup status tracking model."""
    __tablename__ = "backup_file_status"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("backup_nodes.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    remote_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=True, comment="MD5 or SHA256")
    status = Column(
        SQLEnum(FileBackupStatus, values_callable=lambda x: [e.value for e in x]),
        default=FileBackupStatus.PENDING,
        nullable=False
    )
    last_sync_at = Column(DateTime, nullable=True)
    error_message = Column(String(500), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    node = relationship("BackupNode", back_populates="file_statuses")
    image = relationship("Image")

    def __repr__(self):
        return f"<BackupFileStatus(id={self.id}, node_id={self.node_id}, image_id={self.image_id}, status={self.status})>"


class BackupLog(Base):
    """Backup operation log model."""
    __tablename__ = "backup_logs"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("backup_nodes.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(
        SQLEnum(BackupTaskType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status = Column(
        SQLEnum(BackupTaskStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    
    # Statistics
    files_total = Column(Integer, default=0)
    files_success = Column(Integer, default=0)
    files_failed = Column(Integer, default=0)
    bytes_transferred = Column(BigInteger, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Details
    error_details = Column(Text, nullable=True, comment="JSON array of errors")
    triggered_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="Admin user ID")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    node = relationship("BackupNode", back_populates="logs")
    user = relationship("User")

    def __repr__(self):
        return f"<BackupLog(id={self.id}, node_id={self.node_id}, task_type={self.task_type}, status={self.status})>"
