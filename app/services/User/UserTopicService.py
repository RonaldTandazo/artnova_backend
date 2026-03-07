from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Users.UserTopic import UserTopic
from app.models.General.Topic import Topic
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import and_, delete
from app.graphql.UserSkills.UserSkillsPayloads import UserTopicPayload

class UserTopicService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def getUserTopics(self, userId):
        try:            
            result = await self.db.execute(
                select(
                    UserTopic.topic_id,
                    UserTopic.user_id,
                    Topic.name.label('topic')
                )
                .join(
                    Topic, 
                    and_(
                        UserTopic.topic_id == Topic.topic_id,
                        Topic.status == "A"
                    )
                )
                .filter(and_(UserTopic.user_id == userId, UserTopic.status == "A"))
            )

            records = result.mappings().all()

            user_topics_list = [
                UserTopicPayload(
                    userId = item['user_id'],
                    topicId = item['topic_id'],
                    name = item['topic']
                )
                for item in records
            ]
    
            return {"ok": True, "message": "User Topics", "code": 201, "data": user_topics_list}
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
        
    async def deleteUserTopics(self, userId, categoryIds):
        try:
            await self.db.execute(
                delete(UserTopic)
                .where(
                    and_(
                        UserTopic.user_id == userId,
                        UserTopic.topic_id.not_in(categoryIds),
                        UserTopic.status == "A"
                    )
                )
            )
            await self.db.flush()
    
            return {"ok": True, "message": "Deleted User Topics", "code": 201, "data": None}
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
        
    async def deleteAllUserTopics(self, userId):
        try:            
            await self.db.execute(
                delete(UserTopic)
                .where(
                    and_(
                        UserTopic.user_id == userId,
                        UserTopic.status == "A"
                    )
                )
            )
            await self.db.flush()
    
            return {"ok": True, "message": "Deleted All User Topics", "code": 201, "data": None}
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
        
    async def validateUserTopic(self, userId, topicId):
        try:            
            result = await self.db.execute(
                select(UserTopic)
                .filter(
                    and_(
                        UserTopic.user_id == userId,
                        UserTopic.topic_id == topicId,
                        UserTopic.status == "A"
                    )
                )
            )

            existing_record = result.scalar_one_or_none()

            validation = True if existing_record else False 

            return {"ok": True, "message": "Validated User Topic", "code": 201, "data": validation}
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
        
    async def storeUserTopics(self, userId, topicIds, terminal, ip):
        try:
            user_topics_to_add = []
            for topic_id in topicIds: 
                user_topics_to_add.append(
                    UserTopic(
                        user_id=userId,
                        topic_id=topic_id,
                        ip=ip,
                        terminal=terminal
                    )
                )

            self.db.add_all(user_topics_to_add)
            await self.db.flush()
    
            return {"ok": True, "message": "Stored User Topics", "code": 201, "data": None}
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