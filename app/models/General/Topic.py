from sqlalchemy import Column, Integer, String
from app.models.base import AuditBase, Base
from sqlalchemy.orm import relationship

class Topic(AuditBase, Base):
    __tablename__ = "topics"

    topic_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), index=True, nullable=False)

    artwork_topics = relationship("ArtworkTopic", back_populates="topic")