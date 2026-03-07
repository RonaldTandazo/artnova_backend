from app.config.logger import logger
from sqlalchemy import and_, asc
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkOwner import ArtworkOwner
from app.models.Artworks.Artwork import Artwork
from app.models.Users.User import User
from app.models.Artworks.ArtworkThumbnail import ArtworkThumbnail
from app.models.Artworks.ArtworkSchedule import ArtworkSchedule
from typing import Any
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, delete

class ArtworkOwnerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, artworkId: int, userId: int, ip: str, terminal: Any):
        try:
            artwork_user = ArtworkOwner(
                artwork_id=artworkId,
                user_id=userId,
                ip=ip,
                terminal=terminal
            )
            self.db.add(artwork_user)
            await self.db.flush()

            return {"ok": True, "message": "Artwork Owner Saved Successfully", "code": 201, "data": artwork_user}

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
        
    async def getArtVerseArtworks(self):
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
                .select_from(ArtworkOwner)
                .join(User, and_(ArtworkOwner.user_id == User.user_id))
                .join(Artwork, and_(ArtworkOwner.artwork_id == Artwork.artwork_id, Artwork.status == "A", Artwork.publishing_id == 2))
                .outerjoin(ArtworkThumbnail, and_(Artwork.artwork_id == ArtworkThumbnail.artwork_id, ArtworkThumbnail.status == "A"))
                .where(and_(ArtworkOwner.status == "A"))
                .order_by(asc(Artwork.created_at))
            )

            rows = result.mappings().all()

            artworks = [
                {
                    "artwork_id": row['artwork_id'],
                    "title": row['title'],
                    "thumbnail": row['thumbnail'],
                    "publishingId": row['publishingId'],
                    "hasImages": row['hasImages'],
                    "hasVideos": row['hasVideos'],
                    "has3DFile": row['has3DFile'],
                    "createdAt": row['createdAt'],
                    "owner": row['owner'],
                    "avatar": row['avatar'],
                }
                for row in rows
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
        
    async def getUserArtworks(self, userId: int):
        try:
            result = await self.db.execute(
                select(
                    Artwork.artwork_id.label("artworkId"),
                    Artwork.title.label("title"),
                    Artwork.publishing_id.label("publishingId"),
                    ArtworkThumbnail.filename.label("thumbnail"),
                    ArtworkSchedule.schedule_date,
                    ArtworkSchedule.schedule_time
                )
                .select_from(ArtworkOwner)
                .join(Artwork, and_(ArtworkOwner.artwork_id == Artwork.artwork_id, Artwork.status == "A"))
                .outerjoin(ArtworkThumbnail, and_(Artwork.artwork_id == ArtworkThumbnail.artwork_id, ArtworkThumbnail.status == "A"))
                .outerjoin(ArtworkSchedule, and_(Artwork.artwork_id == ArtworkSchedule.artwork_id, ArtworkSchedule.status == "A"))
                .where(and_(ArtworkOwner.status == "A", ArtworkOwner.user_id == userId))
                .order_by(asc(Artwork.created_at))
            )

            rows = result.mappings().all()

            artworks = [
                {
                    "artworkId": row['artworkId'],
                    "title": row['title'],
                    "thumbnail": row['thumbnail'],
                    "publishingId": row['publishingId'],
                    "scheduleDate": row['schedule_date'],
                    "scheduleTime": row['schedule_time'],
                }
                for row in rows
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
        
    async def validateArtworksOwner(self, userId: int, ArtworkIds: list[int]):
        try:
            result = await self.db.execute(
                select(
                    ArtworkOwner.artwork_id
                )
                .where(
                    and_(
                        ArtworkOwner.status == "A",
                        ArtworkOwner.user_id == userId,
                        ArtworkOwner.artwork_id.in_(ArtworkIds)
                    )
                )
            )

            owned_ids = list(result.scalars().all())
            missing_ids = list(set(ArtworkIds) - set(owned_ids))
            all_valid = len(missing_ids) == 0 

            return {
                "ok": True,
                "message": "Validation Done",
                "code": 201,
                "data": {
                    "all_valid": all_valid,
                    "owned_ids": owned_ids,
                    "missing_ids": missing_ids
                }
            }
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
                delete(ArtworkOwner)
                .where(
                    and_(
                        ArtworkOwner.artwork_id.in_(artworkIds),
                        ArtworkOwner.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Owners Deleted Successfully", "code": 201, "data": None}

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