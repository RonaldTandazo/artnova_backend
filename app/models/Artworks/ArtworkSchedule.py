from sqlalchemy import Column, Integer, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkSchedule(AuditBase, Base):
    __tablename__ = "artwork_schedule"

    artwork_schedule_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    publishing_id_target = Column(Integer, ForeignKey("publishing.publishing_id"), nullable=False)
    schedule_date = Column(Date, nullable=False)
    schedule_time = Column(Time, nullable=False)

    artwork = relationship("Artwork")