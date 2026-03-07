from app.config.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError, WriteConcernError
from app.models.Chats.ChatMessage import ChatMessage
from typing import Any
from bson.objectid import ObjectId

class MessageService:
    COLLECTION_NAME = "chat_messages"

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection(self.COLLECTION_NAME)
        
    async def setMessage(self, chatId: str, userId: int, typeMessage: str, message: str, createdAt: str, ip: str, terminal: Any):
        try:
            new_chat_message_model = ChatMessage(
                chat_id=chatId,
                user_id=userId,
                type_message=typeMessage,
                message=message,
                created_at=createdAt,
                ip=ip,
                terminal=terminal
            )

            document_data = new_chat_message_model.model_dump(by_alias=True, exclude_none=True)
            result = await self.collection.insert_one(document_data)

            new_id_str = str(result.inserted_id)

            return {"ok": True, "message": "Chat Message Set", "code": 201, "data": new_id_str}
        except Exception as e:
            error_mapping = {
                WriteConcernError: (400, "Database integrity error"),
                PyMongoError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def getMessageById(self, messageId: str):
        try:
            query = {
                "_id": ObjectId(messageId),
                "status": "A" 
            }

            message_document = await self.collection.find_one(query)

            return {"ok": True, "message": "Chat Message Got", "code": 201, "data": message_document}
        except Exception as e:
            error_mapping = {
                WriteConcernError: (400, "Database integrity error"),
                PyMongoError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def deleteMessagesByChatId(self, chatId: str):
        try:
            query = {
                "chat_id": ObjectId(chatId),
                "status": "A"
            }

            message_document = await self.collection.delete_many(query)

            return {"ok": True, "message": "Chat Messages Deleted", "code": 201, "data": message_document}
        except Exception as e:
            error_mapping = {
                WriteConcernError: (400, "Database integrity error"),
                PyMongoError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}