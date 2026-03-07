from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkTopic import ArtworkTopic
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import delete, and_

class ArtworkTopicService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, artworkId, topicIds, ip, terminal):
        try:
            artwork_topics = []
            for topic_id in topicIds:
                artwork_topic = ArtworkTopic(
                    artwork_id=artworkId,
                    topic_id=topic_id,
                    ip=ip,
                    terminal=terminal
                )
                artwork_topics.append(artwork_topic)
            
            self.db.add_all(artwork_topics)
            await self.db.flush()

            return {"ok": True, "message": "Artwork Topics Saved Successfully", "code": 201, "data": artwork_topics}

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
                delete(ArtworkTopic)
                .where(
                    and_(
                        ArtworkTopic.artwork_id.in_(artworkIds),
                        ArtworkTopic.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Topics Deleted Successfully", "code": 201, "data": None}

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