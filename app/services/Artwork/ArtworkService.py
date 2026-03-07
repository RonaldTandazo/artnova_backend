from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.Artwork import Artwork
from app.models.Artworks.ArtworkCategory import ArtworkCategory
from app.models.Artworks.ArtworkSoftware import ArtworkSoftware
from app.models.Artworks.ArtworkTopic import ArtworkTopic
from app.models.Artworks.ArtworkOwner import ArtworkOwner
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.graphql.Artwork.ArtworkPayloads import StandardPayload
from app.graphql.Artwork.ArtworkPayloads import ArtworkOwnerPayload
from sqlalchemy.future import select
from sqlalchemy import and_, delete
from sqlalchemy.orm import selectinload

class ArtworkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, title, description, matureContent, has_images, has_videos, has_3d_file, ip, terminal, publishing = 3):
        try:
            artwork = Artwork(
                title=title,
                description=description,
                mature_content=matureContent,
                publishing_id=publishing,
                has_images=has_images,
                has_videos=has_videos,
                has_3d_file=has_3d_file,
                ip=ip,
                terminal=terminal
            )
            self.db.add(artwork)
            await self.db.flush()

            return {"ok": True, "message": "Artwork Saved Successfully", "code": 201, "data": artwork}

        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def getArtworkDetails(self, artworkId):
        try:
            result = await self.db.execute(
                select(Artwork)
                .filter(and_(Artwork.artwork_id == artworkId, Artwork.status == "A"))
                .options(
                    selectinload(Artwork.artwork_owner).selectinload(ArtworkOwner.user), 
                    selectinload(Artwork.artwork_categories).selectinload(ArtworkCategory.category), 
                    selectinload(Artwork.artwork_softwares).selectinload(ArtworkSoftware.software),
                    selectinload(Artwork.artwork_topics).selectinload(ArtworkTopic.topic),
                    selectinload(Artwork.artwork_thumbnail),
                    selectinload(Artwork.artwork_videos),
                    selectinload(Artwork.artwork_images)
                )
            )
            artwork = result.scalar_one_or_none()

            if not artwork:
                return {"ok": False, "error": "Artwork Details Not Found", "code": 404}
            
            owner = artwork.artwork_owner.user
            categories = artwork.artwork_categories
            topics = artwork.artwork_topics
            softwares = artwork.artwork_softwares

            artwork = {
                "artwork_id": artwork.artwork_id,
                "title": artwork.title,
                "description": artwork.description,
                "mature_content": artwork.mature_content,
                "categories": [StandardPayload(value=category.category_id, label=category.category.name) for category in categories],
                "topics": [StandardPayload(value=topic.topic_id, label=topic.topic.name) for topic in topics],
                "softwares": [StandardPayload(value=software.software_id, label=software.software.name) for software in softwares],
                "publishing_id": artwork.publishing_id,
                "thumbnail": artwork.artwork_thumbnail.filename if artwork.artwork_thumbnail else None,
                "images": [image.filename for image in artwork.artwork_images],
                "videos": [video.filename for video in artwork.artwork_videos],
                "owner": ArtworkOwnerPayload(userId=owner.user_id, username=owner.username, avatar=owner.avatar),
                "created_at": artwork.created_at,
            }

            return {"ok": True, "message": "Artwork Details Found", "code": 201, "data": artwork}
        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def deleteByArtWorks(self, artworkIds: list[int]):
        try:
            await self.db.execute(
                delete(Artwork)
                .where(
                    and_(
                        Artwork.artwork_id.in_(artworkIds),
                        Artwork.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Deleted Successfully", "code": 201, "data": None}

        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}