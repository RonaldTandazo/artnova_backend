from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkThumbnail(AuditBase, Base):
    __tablename__ = "artwork_thumbnail"

    artwork_thumbnail_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    filename = Column(String(50), nullable=False)
    thumbnail_name = Column(String(50), nullable=False)
    
    artwork = relationship("Artwork")