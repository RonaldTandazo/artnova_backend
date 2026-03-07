from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkThumbnail import ArtworkThumbnail
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, delete, select

class ArtworkThumbnailService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, artworkId, filename, thumbnail_name, ip, terminal):
        try:
            artwork_thumbnail = ArtworkThumbnail(
                artwork_id=artworkId,
                filename=filename,
                thumbnail_name=thumbnail_name,
                ip=ip,
                terminal=terminal
            )
            self.db.add(artwork_thumbnail)
            await self.db.flush()

            return {"ok": True, "message": "Artwork Thumbnail Saved Successfully", "code": 201, "data": artwork_thumbnail}

        except Exception as e:
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
            result = await self.db.execute(
                select(ArtworkThumbnail.filename)
                .where(
                    and_(
                        ArtworkThumbnail.artwork_id.in_(artworkIds),
                        ArtworkThumbnail.status == "A"
                    )
                )
            )

            filenames = result.scalars().all()

            await self.db.execute(
                delete(ArtworkThumbnail)
                .where(
                    and_(
                        ArtworkThumbnail.artwork_id.in_(artworkIds),
                        ArtworkThumbnail.status == "A"
                    )
                )
            )
            
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Thumbnails Deleted Successfully", "code": 201, "data": filenames}

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