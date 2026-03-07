from sqlalchemy import Column, Integer, String
from app.models.base import AuditBase, Base

class Publishing(AuditBase, Base):
    __tablename__ = "publishing"

    publishing_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True, unique=True)
    type = Column(String(20), default= 'select', nullable=True)
