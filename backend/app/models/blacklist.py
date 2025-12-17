from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class BanType(str, enum.Enum):
    TEMPORARY = "TEMPORARY"
    PERMANENT = "PERMANENT"


class AppealStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # Removed unique constraint
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    reason = Column(String(500), nullable=False)
    # Use values_callable to match MySQL uppercase enum values
    ban_type = Column(
        Enum(BanType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BanType.TEMPORARY
    )
    expires_at = Column(DateTime, nullable=True)  # NULL for permanent ban
    violation_count = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Lift fields - for tracking unban history
    lifted_at = Column(DateTime, nullable=True)  # When the ban was lifted
    lifted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    lift_reason = Column(String(500), nullable=True)  # Why it was lifted

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="bans")
    admin = relationship("User", foreign_keys=[created_by])
    lifter = relationship("User", foreign_keys=[lifted_by])
    appeals = relationship("BanAppeal", back_populates="blacklist_entry", cascade="all, delete-orphan")

    @property
    def is_active(self) -> bool:
        """Check if ban is currently active."""
        # If lifted, not active
        if self.lifted_at is not None:
            return False
        # Permanent ban is always active (until lifted)
        if self.ban_type == BanType.PERMANENT:
            return True
        # Temporary ban: check expiry
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at


class ViolationLog(Base):
    __tablename__ = "violation_logs"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="SET NULL"), nullable=True)
    violation_type = Column(String(50), nullable=False, index=True)  # audit_failed, rate_limit_exceeded, etc.
    details = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", backref="violations")
    image = relationship("Image", backref="violations")


class BanAppeal(Base):
    __tablename__ = "ban_appeals"

    id = Column(Integer, primary_key=True, index=True)
    blacklist_id = Column(Integer, ForeignKey("blacklist.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)  # Appeal reason from user
    # Use values_callable to match MySQL uppercase enum values
    status = Column(
        Enum(AppealStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AppealStatus.PENDING,
        index=True
    )
    admin_response = Column(Text, nullable=True)
    handled_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    handled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    blacklist_entry = relationship("Blacklist", back_populates="appeals")
    user = relationship("User", foreign_keys=[user_id], backref="appeals")
    admin = relationship("User", foreign_keys=[handled_by])
