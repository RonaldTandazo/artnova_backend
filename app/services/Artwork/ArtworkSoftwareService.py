from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Artworks.ArtworkSoftware import ArtworkSoftware
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import delete, and_

class ArtworkSoftwareService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store(self, artworkId, softwareIds, ip, terminal):
        try:
            artwork_softwares = []
            for software_id in softwareIds:
                artwork_software = ArtworkSoftware(
                    artwork_id=artworkId,
                    software_id=software_id,
                    ip=ip,
                    terminal=terminal
                )
                artwork_softwares.append(artwork_software)
            
            self.db.add_all(artwork_softwares)
            await self.db.flush()

            return {"ok": True, "message": "Artwork Softwares Saved Successfully", "code": 201, "data": artwork_softwares}

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
                delete(ArtworkSoftware)
                .where(
                    and_(
                        ArtworkSoftware.artwork_id.in_(artworkIds),
                        ArtworkSoftware.status == "A"
                    )
                )
            )
            await self.db.flush()

            return {"ok": True, "message": "ArtWorks Softwares Deleted Successfully", "code": 201, "data": None}

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