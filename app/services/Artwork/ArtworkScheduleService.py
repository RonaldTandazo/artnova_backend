from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkSchedule import ArtworkSchedule
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import delete, and_, update
from datetime import datetime, timezone
from sqlalchemy.future import select

class ArtworkScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def getPendingArtworks(self):
        try:
            now = datetime.now(timezone.utc)

            result = await self.db.execute(
                select(ArtworkSchedule)
                .filter(
                    ArtworkSchedule.status == "A",
                    ArtworkSchedule.schedule_status == "Scheduled",
                    ArtworkSchedule.schedule_at <= now
                )
            )
            schedules = result.scalars().all()

            return {"ok": True, "message": "Artwork Pendings Got", "code": 201, "data": schedules}

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

    async def store(self, artworkId: int,  publishingIdTarget: int, scheduleAt: datetime, ip, terminal):
        try:
            schedule = ArtworkSchedule(
                artwork_id=artworkId,
                publishing_id_target=publishingIdTarget,
                schedule_at=scheduleAt,
                ip=ip,
                terminal=terminal
            )
            self.db.add(schedule)
            await self.db.flush()

            return {"ok": True, "message": "Artwork Schedule Saved Successfully", "code": 201, "data": schedule}

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
            await self.db.execute(
                delete(ArtworkSchedule)
                .where(
                    and_(
                        ArtworkSchedule.artwork_id.in_(artworkIds),
                        ArtworkSchedule.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Schedule Deleted Successfully", "code": 201, "data": None}

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
    
    async def markAsPublished(self, schedule_id):
        try:
            await self.db.execute(
                update(ArtworkSchedule)
                .where(ArtworkSchedule.artwork_schedule_id == schedule_id)
                .values(schedule_status="Published")
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Schedule Marked Published", "code": 201, "data": None}

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