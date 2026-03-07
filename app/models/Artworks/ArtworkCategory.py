from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkCategory(AuditBase, Base):
    __tablename__ = "artwork_categories"

    artwork_category_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)

    artwork = relationship("Artwork", back_populates="artwork_categories")
    category = relationship(
        "Category", 
        back_populates="artwork_categories", 
        primaryjoin="and_(ArtworkCategory.category_id == Category.category_id, Category.status == 'A')"
    )