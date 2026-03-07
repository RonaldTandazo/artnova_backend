from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkUserFavorite import ArtworkUserFavorite
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, delete

class ArtworkUserFavoriteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, userId: int, artworkId: int, ip, terminal):
        try:
            favorite = ArtworkUserFavorite(
                artwork_id=artworkId,
                user_id=userId,
                ip=ip,
                terminal=terminal
            )
            self.db.add(favorite)
            await self.db.flush()

            return {"ok": True, "message": "Favorite Artwork Saved Successfully", "code": 201, "data": favorite}

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
        
    async def deleteByUserAndArtWork(self, userId: int, artworkId: int):
        try:
            await self.db.execute(
                delete(ArtworkUserFavorite)
                .where(
                    and_(
                        ArtworkUserFavorite.user_id == userId,
                        ArtworkUserFavorite.artwork_id == artworkId,
                        ArtworkUserFavorite.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "Favorite ArtWork Deleted Successfully", "code": 201, "data": None}

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
                delete(ArtworkUserFavorite)
                .where(
                    and_(
                        ArtworkUserFavorite.artwork_id.in_(artworkIds),
                        ArtworkUserFavorite.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Favorites Deleted Successfully", "code": 201, "data": None}

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