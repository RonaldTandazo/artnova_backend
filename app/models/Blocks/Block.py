from app.models.base import Base, AuditBase
from sqlalchemy import Column, Integer, ForeignKey

class Block(AuditBase, Base):
    __tablename__ = "blocks"

    block_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    blocker_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    blocked_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

