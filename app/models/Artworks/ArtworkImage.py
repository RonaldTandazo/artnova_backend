from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkImage(AuditBase, Base):
    __tablename__ = "artwork_image"

    artwork_image_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    filename = Column(String(50), nullable=False)
    image_name = Column(String(50), nullable=False)

    artwork = relationship("Artwork")