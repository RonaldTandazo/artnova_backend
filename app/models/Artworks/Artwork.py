from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, AuditBase

class Artwork(AuditBase, Base):
    __tablename__ = "artworks"

    artwork_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(50), index=True, nullable=False)
    description = Column(String(255), nullable=True)
    mature_content = Column(Boolean, nullable=False, default=False)
    publishing_id = Column(Integer, ForeignKey("publishing.publishing_id"), nullable=False)
    has_images = Column(Boolean, nullable=True, default=False)
    has_videos = Column(Boolean, nullable=True, default=False)
    has_3d_file = Column(Boolean, nullable=True, default=False)

    publishing = relationship("Publishing")
    artwork_thumbnail = relationship(
        "ArtworkThumbnail", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkThumbnail.artwork_id, ArtworkThumbnail.status == 'A')", 
        uselist=False
    )

    artwork_owner = relationship(
        "ArtworkOwner", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkOwner.artwork_id, ArtworkOwner.status == 'A')", 
        uselist=False
    )

    artwork_categories = relationship(
        "ArtworkCategory", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkCategory.artwork_id, ArtworkCategory.status == 'A')",
        uselist=True
    )
    
    artwork_softwares = relationship(
        "ArtworkSoftware", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkSoftware.artwork_id, ArtworkSoftware.status == 'A')",
        uselist=True
    )

    artwork_topics = relationship(
        "ArtworkTopic", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkTopic.artwork_id, ArtworkTopic.status == 'A')",
        uselist=True
    )
    
    artwork_images = relationship(
        "ArtworkImage", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkImage.artwork_id, ArtworkImage.status == 'A')",
        uselist=True
    )
    
    artwork_videos = relationship(
        "ArtworkVideo", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkVideo.artwork_id, ArtworkVideo.status == 'A')",
        uselist=True
    )

    artwork_schedule = relationship(
        "ArtworkSchedule", 
        back_populates="artwork", 
        primaryjoin="and_(Artwork.artwork_id == ArtworkSchedule.artwork_id, ArtworkSchedule.status == 'A')", 
        uselist=False
    )