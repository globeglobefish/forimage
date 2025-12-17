from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Action info
    action = Column(String(50), nullable=False)  # login, upload, delete, admin_action, etc.
    resource_type = Column(String(50), nullable=True)  # user, image, album, settings
    resource_id = Column(Integer, nullable=True)
    
    # Actor info
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    
    # Details
    details = Column(Text, nullable=True)  # JSON string with additional info
    status = Column(String(20), default="success")  # success, failure
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action})>"
