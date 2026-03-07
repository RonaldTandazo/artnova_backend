from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Users.UserSoftware import UserSoftware
from app.models.General.Software import Software
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import and_, delete
from app.graphql.UserSkills.UserSkillsPayloads import UserSoftwarePayload

class UserSoftwareService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def getUserSoftwares(self, userId):
        try:            
            result = await self.db.execute(
                select(
                    UserSoftware.user_id,
                    UserSoftware.software_id,
                    Software.name.label('software')
                )
                .join(
                    Software, 
                    and_(
                        UserSoftware.software_id == Software.software_id,
                        Software.status == "A"
                    )
                )
                .filter(and_(UserSoftware.user_id == userId, UserSoftware.status == "A"))
            )

            records = result.mappings().all()

            user_softwares_list = [
                UserSoftwarePayload(
                    userId = item['user_id'],
                    softwareId = item['software_id'],
                    name = item['software']
                )
                for item in records
            ]
    
            return {"ok": True, "message": "User Softwares", "code": 201, "data": user_softwares_list}
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
        
    async def deleteUserSoftwares(self, userId, softwareIds):
        try:            
            await self.db.execute(
                delete(UserSoftware)
                .where(
                    and_(
                        UserSoftware.user_id == userId,
                        UserSoftware.software_id.not_in(softwareIds),
                        UserSoftware.status == "A"
                    )
                )
            )
            await self.db.flush()
    
            return {"ok": True, "message": "Deleted User Softwares", "code": 201, "data": None}
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
        
    async def deleteAllUserSoftwares(self, userId):
        try:            
            await self.db.execute(
                delete(UserSoftware)
                .where(
                    and_(
                        UserSoftware.user_id == userId,
                        UserSoftware.status == "A"
                    )
                )
            )
            await self.db.flush()
    
            return {"ok": True, "message": "Deleted All User Softwares", "code": 201, "data": None}
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
        
    async def validateUserSoftware(self, userId, softwareId):
        try:            
            result = await self.db.execute(
                select(UserSoftware)
                .filter(
                    and_(
                        UserSoftware.user_id == userId,
                        UserSoftware.software_id == softwareId,
                        UserSoftware.status == "A"
                    )
                )
            )

            existing_record = result.scalar_one_or_none()

            validation = True if existing_record else False

            return {"ok": True, "message": "Validated User Software", "code": 201, "data": validation}
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
        
    async def storeUserSoftwares(self, userId, softwareIds, terminal, ip):
        try:
            user_softwares_to_add = []
            for software_id in softwareIds: 
                user_softwares_to_add.append(
                    UserSoftware(
                        user_id=userId,
                        software_id=software_id,
                        ip=ip,
                        terminal=terminal
                    )
                )

            self.db.add_all(user_softwares_to_add)
            await self.db.flush()
    
            return {"ok": True, "message": "Stored User Softwares", "code": 201, "data": None}
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