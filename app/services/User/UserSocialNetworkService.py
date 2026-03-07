import datetime
from app.config.logger import logger
from sqlalchemy.future import select
from sqlalchemy import and_, asc, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from app.models.Users.UserSocialNetwork import UserSocialNetwork
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

class UserSocialNetworkService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def getUserSocialMedia(self, userId: int):
        try:            
            result = await self.db.execute(
                select(UserSocialNetwork)
                .options(joinedload(UserSocialNetwork.socialMedia))
                .filter(and_(UserSocialNetwork.user_id == userId, UserSocialNetwork.status == "A"))
                .order_by(asc(UserSocialNetwork.user_social_network_id))
            )

            social_media_list = [
                {
                    "user_social_network_id": item.user_social_network_id,
                    "social_media_id": item.social_media_id,
                    "link": item.link,
                    "network_name": item.socialMedia.name,
                }
                for item in result.scalars().all()
            ]
    
            #if social_media_list:
            return {"ok": True, "message": "User Social Media", "code": 201, "data": social_media_list}

            #return {"ok": False, "error": "Social Media Not Found", "code": 404}
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
        
    async def getUserSocialMediaById(self, userSocialNetworkId: int):
        try:            
            result = await self.db.execute(
                select(UserSocialNetwork)
                .filter(and_(UserSocialNetwork.user_social_network_id == userSocialNetworkId, UserSocialNetwork.status == "A"))
            )
            item = result.scalars().first()

            if not item:
                return {"ok": False, "error": "Social Network Not Found", "code": 404}

            return {"ok": True, "message": "Social Network Found", "code": 201, "data": item}
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
        
    async def store(self, userId: int, socialNetworkId: int, link: str, ip: str, terminal: Any):
        try:            
            item = UserSocialNetwork(
                user_id=userId,
                social_media_id=socialNetworkId,
                link=link,
                ip=ip,
                terminal=terminal
            )
            self.db.add(item)
            await self.db.flush()

            return {"ok": True, "message": "Social Network Stored", "code": 201, "data": item}
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
        
    async def update(self, item: UserSocialNetwork, socialNetworkId: int, link: str):
        try:            
            item.social_media_id = socialNetworkId
            item.link = link
            item.updated_at=datetime.datetime.now()
            await self.db.flush()

            return {"ok": True, "message": "Social Network Updated", "code": 201, "data": item}
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
        
    async def remove(self, item: UserSocialNetwork):
        try:
            await self.db.execute(delete(UserSocialNetwork).where(UserSocialNetwork.user_social_network_id == item.user_social_network_id))
            await self.db.flush()

            return {"ok": True, "message": "Social Network Unlinked", "code": 201, "data": None}
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