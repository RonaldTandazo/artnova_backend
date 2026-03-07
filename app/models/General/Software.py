from sqlalchemy import Column, Integer, String
from app.models.base import AuditBase, Base
from sqlalchemy.orm import relationship

class Software(AuditBase, Base):
    __tablename__ = "softwares"

    software_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True, unique=True, nullable=False)
    image = Column(String(255), default=None, nullable=True)

    artwork_softwares = relationship("ArtworkSoftware", back_populates="software")