from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkOwner(AuditBase, Base):
    __tablename__ = "artwork_owner"

    artwork_owner_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    artwork = relationship("Artwork")
    user = relationship(
        "User", 
        back_populates="artwork_owner", 
        primaryjoin="and_(ArtworkOwner.user_id == User.user_id, User.status == 'A')",
        uselist=False
    )