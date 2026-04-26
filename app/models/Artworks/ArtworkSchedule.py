from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base


class ArtworkSchedule(AuditBase, Base):
    __tablename__ = "artwork_schedule"

    artwork_schedule_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    publishing_id_target = Column(Integer, ForeignKey("publishing.publishing_id"), nullable=False)
    schedule_status = Column(String(15), default='Scheduled', nullable=False)
    schedule_at = Column(DateTime(timezone=True), nullable=False)

    artwork = relationship("Artwork")