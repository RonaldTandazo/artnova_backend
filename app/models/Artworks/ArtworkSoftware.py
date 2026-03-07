from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkSoftware(AuditBase, Base):
    __tablename__ = "artwork_softwares"

    artwork_software_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    software_id = Column(Integer, ForeignKey("softwares.software_id"), nullable=False)

    artwork = relationship("Artwork")
    software = relationship(
        "Software",
        back_populates="artwork_softwares",
        primaryjoin="and_(ArtworkSoftware.software_id == Software.software_id, Software.status == 'A')"    
    )