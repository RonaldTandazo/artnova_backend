from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.ArtworkModel.ArtworkModel import ArtworkModel
from app.graphql.Artwork.ArtworkPayloads import ModelSettings
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Any, Dict

class ArtworkModelService:
    COLLECTION_NAME = "artwork_model"
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection(self.COLLECTION_NAME)

    async def store(self, artworkId: int, ownerId: int, mainFile: str, resources: list[str], settings, ip: str, terminal: Any):
        try:
            new_artwork_model = ArtworkModel(
                artwork_id=artworkId,
                owner_id=ownerId,
                main_file=mainFile,
                resources=resources,
                settings=settings,
                ip=ip,
                terminal=terminal
            )

            document_data = new_artwork_model.model_dump(by_alias=True, exclude_none=True)
            result = await self.collection.insert_one(document_data)

            new_id_str = str(result.inserted_id)

            return {"ok": True, "message": "Artwork Model Saved Successfully", "code": 201, "data": new_id_str}

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
        
    async def getArtworkModel(self, artworkId: int):
        try:
            pipeline: list[Dict[str, Any]] = [
                {"$match": {"artwork_id": artworkId, "status": "A"}},

                {"$project": {
                    "_id": 0,
                    "main_file": 1,
                    "resources": 1,
                    "settings": 1,
                }},
            ]

            cursor = self.collection.aggregate(pipeline)
            document = None
            async for doc in cursor:
                document = doc
                break

            data = {
                'mainFile': document['main_file'],
                'resources': document['resources'],
                'settings': ModelSettings(**document['settings']),
            }

            return {"ok": True, "message": "ArtWork Model Retrieved", "code": 200, "data": data}
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

            return {"ok": True, "message": "ArtWorks' Model Deleted Successfully", "code": 201, "data": None}

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
 