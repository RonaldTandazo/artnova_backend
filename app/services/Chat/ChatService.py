from app.config.logger import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError, WriteConcernError
from app.graphql.Chat.ChatPayloads import ChatMessagePayload
from app.models.Chats.Chat import Chat
from typing import Any
from bson.objectid import ObjectId
from datetime import datetime
from app.graphql.Chat.ChatInputs import MessageInput

class ChatService:
    COLLECTION_NAME = "chats"
    MESSAGE_COLLECTION_NAME = "chat_messages"

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection(self.COLLECTION_NAME)
        self.message_collection = db.get_collection(self.MESSAGE_COLLECTION_NAME)

    async def getChats(self, userId: int, limit: int, offset: int):
        try:
            pipeline = [
                {
                    "$match": {
                        "users": userId,
                        "status": "A" 
                    }
                },

                {
                    "$sort": {
                        "updated_at": -1 
                    }
                },

                { "$skip": offset },

                { "$limit": limit },
                
                {
                    "$project": {
                        "_id": 0,
                        "chatId": "$_id",
                        "last_message": 1,
                        "artistId": {
                            "$arrayElemAt": [
                                {
                                    "$filter": {
                                        "input": "$users",
                                        "as": "uid",
                                        "cond": { "$ne": ["$$uid", userId] }
                                    }
                                },
                                0
                            ]
                        }
                    }
                }
            ]

            chats_cursor = self.collection.aggregate(pipeline)
            chats = await chats_cursor.to_list(length=None)

            response = chats

            return {"ok": True, "message": "Artist Chat Got", "code": 201, "data": response}
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
        
    async def getChatByUsers(self, userA: int, userB: int):
        try:
            response = {
                "chatId": None
            }

            users_list = sorted([userA, userB])
            query = {
                "users": users_list,
                "status": "A" 
            }

            chat_document = await self.collection.find_one(query)

            if chat_document:
                chatId = str(chat_document["_id"])

                response = {
                    "chatId": chatId
                }

            return {"ok": True, "message": "Chat Got", "code": 201, "data": response}
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

    async def getChat(self, chatId: str, limit: int, offset: int):
        try:
            query = {
                "_id": ObjectId(chatId),
                "status": "A" 
            }
            
            pipeline = [
                {"$match": query},
                
                {
                    "$lookup": {
                        "from": self.MESSAGE_COLLECTION_NAME,
                        "localField": "messages",
                        "foreignField": "_id",
                        "pipeline": [
                            {"$sort": {"created_at": -1}}, 
                            {"$skip": offset},
                            {"$limit": limit + 1}, 
                            {"$sort": {"created_at": 1}}, 
                        ],
                        "as": "full_messages"
                    }
                },
                
                {
                    "$project": {
                        "chatId": {"$toString": "$_id"},
                        "messages": {
                            "$map": {
                                "input": "$full_messages",
                                "as": "msg",
                                "in": {
                                    "chatId": {"$toString": "$_id"},
                                    "messageId": {"$toString": "$$msg._id"},
                                    "userId": "$$msg.user_id",
                                    "typeMessage": "$$msg.type_message",
                                    "message": "$$msg.message",
                                    "createdAt": "$$msg.created_at",
                                    "date": {
                                        "$dateToString": {
                                            "format": "%Y-%m-%d %H:%M",
                                            "date": "$$msg.created_at"
                                        }
                                    }
                                }
                            }
                        },
                        "_id": 0
                    }
                }
            ]

            result = None
            cursor = self.collection.aggregate(pipeline)
            
            async for doc in cursor:
                result = doc
                break

            if result:
                messages = result["messages"]
                response = {
                    "chatId": result['chatId'],
                    "messages": [ChatMessagePayload(chatId=result['chatId'], messageId=message['messageId'], userId=message['userId'], typeMessage=message['typeMessage'], message=message['message'], createdAt=message['createdAt'], date=message["date"]) for message in messages[:limit]], 
                    "hasMore": len(messages) > limit
                }

            return {"ok": True, "message": "Artist Chat Got", "code": 201, "data": response}
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
        
    async def setChat(self, userA: int, userB: int, ip: str, terminal: Any):
        try:
            users = sorted([userA, userB])

            new_chat_model = Chat(
                users=users,
                ip=ip,
                terminal=terminal
            )

            document_data = new_chat_model.model_dump(by_alias=True, exclude_none=True)
            result = await self.collection.insert_one(document_data)

            new_id_str = str(result.inserted_id)

            return {"ok": True, "message": "Artist Chat Set", "code": 201, "data": new_id_str}
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
        
    async def addMessage(self, chatId: str, messageId: str, message: MessageInput):
        try:
            date_utc = datetime.fromisoformat(message.createdAt.replace('Z', '+00:00'))

            last_message = {
                "user_id": message.userId,
                "message": message.message,
                "date": date_utc.date().isoformat(),
                "time": date_utc.strftime("%H:%M")
            }

            filter_query = {"_id": ObjectId(chatId)}

            update_operation = {
                "$push": {
                    "messages": ObjectId(messageId)
                },
                "$set": {
                    "last_message": last_message,
                    "updated_at": datetime.now()
                }
            }

            await self.collection.update_one(
                filter_query,
                update_operation
            )

            return {"ok": True, "message": "Chat Messages Updated", "code": 200, "data": None}
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
        
    async def deleteChat(self, chatId: str):
        try:
            filter_query = {"_id": ObjectId(chatId)}

            await self.collection.delete_one(filter_query)

            return {"ok": True, "message": "Chat Deleted Successfully", "code": 200, "data": None}
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