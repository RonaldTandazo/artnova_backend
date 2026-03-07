from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.ArtworkStatistics.ArtworkStatistics import ArtworkStatistics
from app.models.ArtworkStatistics.ArtworkComment import ArtworkComment
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from bson.objectid import ObjectId
from typing import Dict, Any, Optional, List
from datetime import datetime

class ArtworkStatisticsService:
    COLLECTION_NAME = "artwork_statistics"
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection(self.COLLECTION_NAME)

    async def verifyExistance(self, artworkId: int):
        try:
            data: Dict[str, Optional[Any]] = {"exists": False, "id": None}
            document = await self.collection.find_one({"artwork_id": artworkId}, {"_id": 1})

            if document:
                data["exists"] = True
                data["id"] = str(document["_id"]) 

            return {"ok": True, "message": "Artwork Statistics Verified", "code": 200, "data": data}
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

    async def store(self, artworkId: int, ownerId: int, ip: str, terminal: Any):
        try:
            new_stats_model = ArtworkStatistics(
                artwork_id=artworkId,
                owner_id=ownerId,
                ip=ip,
                terminal=terminal
            )

            document_data = new_stats_model.model_dump(by_alias=True, exclude_none=True)
            result = await self.collection.insert_one(document_data)

            new_id_str = str(result.inserted_id)

            return {"ok": True, "message": "Artwork Stats Saved Successfully", "code": 201, "data": new_id_str}

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

            return {"ok": True, "message": "ArtWorks Stats Deleted Successfully", "code": 201, "data": None}

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
        
    async def addComment(self, documentId: str, comment_data: ArtworkComment):
        try:
            comment_dict = comment_data.model_dump() 
            
            result = await self.collection.update_one(
                {"_id": ObjectId(documentId)},
                {
                    "$push": {"comments": comment_dict},
                    "$inc":  {"stats.comments_amount": 1} 
                },
                upsert=False
            )
            
            return {"ok": True, "message": "Comment Posted Successfully", "code": 201, "data": result}
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
        
    async def deleteComments(self, documentId: str, commentIds: str, userId: int):
        try:            
            await self.collection.update_one(
                {"_id": ObjectId(documentId)},
                {
                    "$pull": {
                        "comments": {
                            "id": {"$in": commentIds},
                            "user_id": userId
                        }
                    },
                    "$inc": {
                        "stats.comments_amount": -1
                    }
                },
                upsert=False
            )
            
            return {"ok": True, "message": "Comment Deleted Successfully", "code": 201, "data": None}
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
        
    async def getArtworkStatistics(self, artworkId: int):
        try:
            pipeline: List[Dict[str, Any]] = [
                {"$match": {"artwork_id": artworkId, "status": "A"}},

                # Stage 2: Filter the main comments array (keeping only active comments)
                {"$project": {
                    "_id": 0,
                    "stats": 1,
                    "comments": {
                        "$filter": {
                            "input": "$comments",
                            "as": "comment",
                            "cond": {
                                "$and": [
                                    {"$eq": ["$$comment.status", "A"]},
                                    {"$setField": {
                                        "field": "replies",
                                        "input": "$$comment",
                                        "value": {
                                            "$filter": {
                                                "input": "$$comment.replies",
                                                "as": "reply",
                                                "cond": {"$eq": ["$$reply.status", "A"]}
                                            }
                                        }
                                    }}
                                ]
                            }
                        }
                    }
                }},
                
                # Stage 3: Iterate over the active comments, filter their replies, and reshape the output
                {"$project": {
                    "stats": 1,
                    "comments": {
                        "$map": {
                            "input": "$comments",
                            "as": "c",
                            "in": {
                                "commentId": "$$c.id",
                                "userId": "$$c.user_id",
                                "username": "$$c.username",
                                "avatar": "$$c.avatar",
                                "comment": "$$c.comment",
                                "likes": "$$c.likes",
                                "dislikes": "$$c.dislikes",
                                "createdAt": {
                                    "$dateToString": {
                                        "format": "%d/%b/%Y",
                                        "date": "$$c.created_at"
                                    }
                                },
                                "replies": {
                                    "$map": {
                                        "input": {
                                            "$filter": {
                                                "input": "$$c.replies",
                                                "as": "reply",
                                                "cond": {"$eq": ["$$reply.status", "A"]}
                                            }
                                        },
                                        "as": "r",
                                        "in": {
                                            "commentId": "$$r.id",
                                            "userId": "$$r.user_id",
                                            "username": "$$r.username",
                                            "avatar": "$$r.avatar",
                                            "comment": "$$r.comment",
                                            "likes": "$$r.likes",
                                            "dislikes": "$$r.dislikes",
                                            "createdAt": {
                                                "$dateToString": {
                                                    "format": "%d/%b/%Y",
                                                    "date": "$$r.created_at"
                                                }
                                            },
                                        }
                                    }
                                }
                            }
                        }
                    }
                }}
            ]

            cursor = self.collection.aggregate(pipeline)
            document = None
            async for doc in cursor:
                document = doc
                break

            artwork_stats = document['stats'] if document else {"views_amount": 0, "likes": [], "dislikes": [], "favorites": [], "comments_amount": 0}
            artwork_comments = document['comments'] if document else []

            data = {
                "stats": artwork_stats,
                "comments": artwork_comments
            }

            return {"ok": True, "message": "ArtWork Statistics Retrieved", "code": 200, "data": data}
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
            pipeline: List[Dict[str, Any]] = [
                {"$match": {"owner_id": userId, "status": "A"}},

                {"$project": {
                    "_id": 0,
                    "artwork_id": 1,
                    "stats": 1,
                }}
            ]

            cursor = self.collection.aggregate(pipeline)
            artworks = []

            async for doc in cursor:
                artwork_stats = doc.get('stats', {
                    "views_amount": 0,
                    "likes": [],
                    "dislikes": [],
                    "favorites": [],
                    "comments_amount": 0
                })

                artworks.append({
                    "artwork_id": doc["artwork_id"],
                    "stats": artwork_stats
                })

            return {"ok": True, "message": "ArtWork Statistics Retrieved", "code": 200, "data": artworks}
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
    
    async def updateArtworkLikes(self, artworkId: int, likes: list[int]):
        try:
            filter_query = {
                "artwork_id": artworkId, 
                "status": 'A'
            }

            update_operation = {
                "$set": {
                    "stats.likes": likes,
                    "updated_at": datetime.now()
                }
            }

            await self.collection.update_one(filter_query, update_operation)

            return {"ok": True, "message": "Artwork Likes Updated", "code": 200, "data": None}
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
        
    async def updateArtworkDisLikes(self, artworkId: int, dislikes: list[int]):
        try:
            filter_query = {
                "artwork_id": artworkId, 
                "status": 'A'
            }

            update_operation = {
                "$set": {
                    "stats.dislikes": dislikes,
                    "updated_at": datetime.now()
                }
            }

            await self.collection.update_one(filter_query, update_operation)

            return {"ok": True, "message": "Artwork DisLikes Updated", "code": 200, "data": None}
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
        
    async def updateArtworkFavorites(self, artworkId: int, favorites: list[int]):
        try:
            filter_query = {
                "artwork_id": artworkId, 
                "status": 'A'
            }

            update_operation = {
                "$set": {
                    "stats.favorites": favorites,
                    "updated_at": datetime.now()
                }
            }

            await self.collection.update_one(filter_query, update_operation)

            return {"ok": True, "message": "Artwork Favorites Updated", "code": 200, "data": None}
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
        
    async def updateCommentLikes(self, artworkId: int, commentId: str, likes: list[int]):
        try:
            filter_query = {
                "artwork_id": artworkId, 
                "status": 'A'
            }

            update_operation = {
                "$set": {
                    "comments.$[comment].likes": likes,
                    "comments.$[comment].updated_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }

            array_filters = [
                {
                    "comment.id": commentId,
                    "comment.status": 'A'
                }
            ]

            await self.collection.update_one(filter_query, update_operation, array_filters=array_filters)

            return {"ok": True, "message": "Comment Likes Updated", "code": 200, "data": None}
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
        
    async def updateCommentDisLikes(self, artworkId: int, commentId: str, dislikes: list[int]):
        try:
            filter_query = {
                "artwork_id": artworkId, 
                "status": 'A'
            }

            update_operation = {
                "$set": {
                    "comments.$[comment].dislikes": dislikes,
                    "comments.$[comment].updated_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            }

            array_filters = [
                {
                    "comment.id": commentId,
                    "comment.status": 'A'
                }
            ]

            await self.collection.update_one(filter_query, update_operation, array_filters=array_filters)

            return {"ok": True, "message": "Comment DisLikes Updated", "code": 200, "data": None}
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
        
    async def updateArtworkViews(self, artworkId: int):
        try:
            filter_query = {
                "artwork_id": artworkId, 
                "status": 'A'
            }

            update_operation = {
                "$inc": {
                    "stats.views_amount": 1
                },
                "$set": {
                    "updated_at": datetime.now()
                }
            }

            await self.collection.update_one(filter_query, update_operation)

            return {"ok": True, "message": "Artwork Views Updated", "code": 200, "data": None}
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
 