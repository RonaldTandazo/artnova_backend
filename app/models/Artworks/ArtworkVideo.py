from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkVideo(AuditBase, Base):
    __tablename__ = "artwork_video"

    artwork_video_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    filename = Column(String(50), nullable=False)
    video_name = Column(String(50), nullable=False)

    artwork = relationship("Artwork")