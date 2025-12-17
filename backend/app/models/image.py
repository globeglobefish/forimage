from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ImageStatus(str, enum.Enum):
    PENDING = "pending"  # Waiting for audit
    APPROVED = "approved"
    REJECTED = "rejected"


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    
    # File info
    filename = Column(String(8), unique=True, index=True, nullable=False)  # 8-char random string
    original_filename = Column(String(255), nullable=False)
    title = Column(String(200), nullable=True)  # User-editable title
    extension = Column(String(10), nullable=False)
    mime_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # In bytes
    file_path = Column(String(500), nullable=False)  # Storage path
    
    # Image dimensions
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Storage info
    storage_type = Column(String(20), default="local")  # local, s3c, oss, cos
    storage_url = Column(String(500), nullable=True)  # CDN/Cloud URL if applicable
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for guest uploads
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)
    guest_ip = Column(String(45), nullable=True)  # Legacy: For guest uploads only
    upload_ip = Column(String(45), nullable=True)  # IP address of uploader (both guest and user)
    
    # Status - use values_callable to match MySQL lowercase enum values
    status = Column(
        SQLEnum(ImageStatus, values_callable=lambda x: [e.value for e in x]),
        default=ImageStatus.APPROVED,
        nullable=False
    )
    audit_result = Column(String(2000), nullable=True)  # Audit API response (JSON)
    
    # Stats
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="images")
    album = relationship("Album", back_populates="images")

    @property
    def full_filename(self) -> str:
        """Get filename with extension (e.g., 'abc123.png')."""
        return f"{self.filename}.{self.extension}"

    @property
    def url(self) -> str:
        """
        Get the public URL for this image.
        
        For cloud storage: returns storage_url (full cloud URL)
        For local storage: returns /uploads/{file_path}
        
        file_path may be:
        - Legacy flat format: "abc123.png"
        - New date-based format: "2025/12/14/abc123.png"
        """
        if self.storage_url:
            return self.storage_url
        # Use file_path which includes date folder structure for new uploads
        # or just filename for legacy uploads
        return f"/uploads/{self.file_path}"

    def __repr__(self):
        return f"<Image(id={self.id}, filename={self.filename})>"
