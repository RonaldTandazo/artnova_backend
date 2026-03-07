from sqlalchemy import Column, Integer, String
from app.models.base import AuditBase, Base

class SocialMedia(AuditBase, Base):
    __tablename__ = "social_media"

    social_media_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True, unique=True, nullable=False)
