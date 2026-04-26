from app.models.base import Base, AuditBase
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Index

class Notification(AuditBase, Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    emitter_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    receipter_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    type = Column(String(50), nullable=False)
    entity = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    image = Column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_notifications_receipter", "receipter_id"),
        Index("idx_notifications_receipter_read", "receipter_id", "is_read"),
        Index("idx_notifications_receipter_created", "receipter_id", "created_at"),
    )