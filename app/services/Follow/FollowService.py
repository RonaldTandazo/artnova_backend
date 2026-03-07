from app.config.logger import logger
from sqlalchemy import and_, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models.Follows.Follow import Follow
from typing import Any

class FollowService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def verifyRelationship(self, followerId: int, followedId: int):
        try:
            result = await self.db.execute(
                select(Follow.follow_id)
                .where(and_(
                    Follow.status == "A", 
                    Follow.followed_id == followedId, 
                    Follow.follower_id == followerId
                ))
                .limit(1)
            )

            follow_id = result.scalars().first()

            relationship_exists = follow_id is not None

            response ={"exists": relationship_exists, "follow_id": follow_id}

            return {"ok": True, "message": "Relationship Verified", "code": 200, "data": response}
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
        
    async def setFollow(self, followerId: int, followedId: int, ip: str, terminal: Any):
        try:
            follow = Follow(
                follower_id=followerId,
                followed_id=followedId,
                ip=ip,
                terminal=terminal 
            )

            self.db.add(follow)
            await self.db.flush()

            return {"ok": True, "message": "Relationship Successfully Stored", "code": 200, "data": follow}
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
        
    async def unsetFollow(self, followId: int):
        try:
            await self.db.execute(
                delete(Follow).where(Follow.follow_id == followId)
            )
            await self.db.flush()

            return {"ok": True, "message": "Relationship Successfully Stored", "code": 200, "data": None}
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