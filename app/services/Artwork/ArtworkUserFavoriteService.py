from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkUserFavorite import ArtworkUserFavorite
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, delete, asc
from sqlalchemy.future import select
from app.models.Users.User import User
from app.models.Artworks.ArtworkThumbnail import ArtworkThumbnail
from app.models.Artworks.Artwork import Artwork
from app.models.Artworks.ArtworkOwner import ArtworkOwner
from app.graphql.Artwork.ArtworkPayloads import ArtworkPayload

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
        
    async def getFavoritesArtworksByUser(self, userId: int):
        try:
            result = await self.db.execute(
                select(
                    Artwork.artwork_id.label("artwork_id"),
                    Artwork.title.label("title"),
                    Artwork.publishing_id.label("publishingId"),
                    Artwork.has_images.label("hasImages"),
                    Artwork.has_videos.label("hasVideos"),
                    Artwork.has_3d_file.label("has3DFile"),
                    Artwork.created_at.label("createdAt"),
                    ArtworkThumbnail.filename.label("thumbnail"),
                    User.username.label("owner"),
                    User.avatar.label("avatar")
                )
                .select_from(ArtworkUserFavorite)
                .join(Artwork, and_(ArtworkUserFavorite.artwork_id == Artwork.artwork_id, Artwork.status == "A", Artwork.publishing_id == 2))
                .outerjoin(ArtworkThumbnail, and_(Artwork.artwork_id == ArtworkThumbnail.artwork_id, ArtworkThumbnail.status == "A"))
                .join(ArtworkOwner, and_(ArtworkOwner.artwork_id == Artwork.artwork_id, ArtworkOwner.status == "A",))
                .join(User, and_(ArtworkOwner.user_id == User.user_id, User.status == "A",))
                .where(and_(ArtworkUserFavorite.status == "A", ArtworkUserFavorite.user_id == userId))
                .order_by(asc(Artwork.created_at))
            )

            rows = result.mappings().all()

            artworks = [
                ArtworkPayload(
                    artworkId=artwork['artwork_id'],
                    title=artwork['title'],
                    thumbnail=artwork['thumbnail'],
                    publishingId=artwork['publishingId'],
                    owner=artwork['owner'],
                    avatar=artwork['avatar'],
                    createdAt=artwork['createdAt'],
                    hasImages=artwork['hasImages'],
                    hasVideos=artwork['hasVideos'],
                    has3DFile=artwork['has3DFile']
                ) for artwork in rows
            ]

            return {"ok": True, "message": "Artworks Found", "code": 201, "data": artworks}
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