from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkCategory import ArtworkCategory
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import delete, and_ 

class ArtworkCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, artworkId, categoryIds, ip, terminal):
        try:
            artwork_categories = []
            for category_id in categoryIds:
                artwork_category = ArtworkCategory(
                    artwork_id=artworkId,
                    category_id=category_id,
                    ip=ip,
                    terminal=terminal
                )
                artwork_categories.append(artwork_category)
            
            self.db.add_all(artwork_categories)
            await self.db.flush()

            return {"ok": True, "message": "Artwork Categories Saved Successfully", "code": 201, "data": artwork_categories}

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
                delete(ArtworkCategory)
                .where(
                    and_(
                        ArtworkCategory.artwork_id.in_(artworkIds),
                        ArtworkCategory.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Categories Deleted Successfully", "code": 201, "data": None}

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