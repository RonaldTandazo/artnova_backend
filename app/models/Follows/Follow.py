from app.models.base import Base, AuditBase
from sqlalchemy import Column, Integer, ForeignKey

class Follow(AuditBase, Base):
    __tablename__ = "follows"

    follow_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    followed_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

