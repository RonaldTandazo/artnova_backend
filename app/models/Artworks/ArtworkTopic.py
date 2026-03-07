from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import AuditBase, Base

class ArtworkTopic(AuditBase, Base):
    __tablename__ = "artwork_topics"

    artwork_topic_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey("artworks.artwork_id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.topic_id"), nullable=False)

    artwork = relationship("Artwork")
    topic = relationship(
        "Topic",
        back_populates="artwork_topics",
        primaryjoin="and_(ArtworkTopic.topic_id == Topic.topic_id, Topic.status == 'A')"
    )