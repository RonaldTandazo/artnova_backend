from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.ArtworkViews.ArtworkViews import ArtworkViews
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

class ArtworkViewsService:
    COLLECTION_NAME = "artwork_views"
    UTC = timezone.utc

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection(self.COLLECTION_NAME)

    async def verifyExistance(self, artworkId: int, userId: int | None, ip: str):
        try:
            data: Dict[str, Optional[Any]] = {"exists": False, "id": None}

            if userId:
                document = await self.collection.find_one(
                    {"artwork_id": artworkId, "user_id": userId}, 
                    {"_id": 1}
                )

                if document:
                    data["exists"] = True
                    data["id"] = str(document["_id"])

            else:
                document = await self.collection.find_one(
                    {"artwork_id": artworkId, "ip": ip},
                    {"_id": 1, "created_at": 1}, 
                    sort=[('created_at', -1)]
                )

                if document:
                    created_at: datetime = document.get("created_at")

                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=self.UTC)

                    now_utc = datetime.now(self.UTC)

                    if now_utc - created_at < timedelta(hours=24):
                        data["exists"] = True
                        data["id"] = str(document["_id"])

            return {"ok": True, "message": "Artwork Views Verified", "code": 200, "data": data}
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

    async def store(self, artworkId: int, userId: int | None, ip: str, terminal: Any):
        try:
            new_views_model = ArtworkViews(
                artwork_id=artworkId,
                user_id=userId,
                ip=ip,
                terminal=terminal
            )

            document_data = new_views_model.model_dump(by_alias=True, exclude_none=True)
            result = await self.collection.insert_one(document_data)

            new_id_str = str(result.inserted_id)

            return {"ok": True, "message": "Artwork Views Saved Successfully", "code": 201, "data": new_id_str}

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
            await self.collection.delete_many(
                {"artwork_id": {"$in": artworkIds}}
            )

            return {"ok": True, "message": "ArtWorks Views Deleted Successfully", "code": 201, "data": None}

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
 