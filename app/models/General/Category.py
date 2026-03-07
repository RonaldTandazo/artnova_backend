from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class Category(AuditBase, Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True, unique=True, nullable=False)

    artwork_categories = relationship("ArtworkCategory", back_populates="category")