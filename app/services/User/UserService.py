from app.config.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from sqlalchemy.future import select
from typing import Any
from app.models.Users.User import User
from app.models.General.Country import Country
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def getUserById(self, userId: int):
        try:
            result = await self.db.execute(select(User).filter(and_(User.user_id == userId, User.status == "A")))
            user = result.scalars().first()

            if not user:
                return {"ok": False, "error": "User Not Found", "code": 404}

            return {"ok": True, "message": "User Found", "code": 201, "data": user}
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
        
    async def getUserByEmail(self, email: str):
        try:
            result = await self.db.execute(select(User).filter(and_(User.email == email, User.status == "A")))
            user = result.scalars().first()

            if not user:
                return {"ok": False, "error": "User Not Found", "code": 404}

            return {"ok": True, "message": "User Found", "code": 201, "data": user}
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
        
    async def getUserByUsername(self, username: str):
        try:
            result = await self.db.execute(select(User).filter(and_(User.username == username, User.status == "A")))
            user = result.scalars().first()

            if not user:
                return {"ok": False, "error": "User Not Found", "code": 404}

            return {"ok": True, "message": "User Found", "code": 201, "data": user}
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

    async def registerUser(self, firstName: str, lastName: str, username: str, email: str, password: str, ip: str, terminal: Any):
        try:
            hashed_password = User.hashPassword(password)
            user = User(
                first_name=firstName,
                last_name=lastName, 
                username=username, 
                email=email, 
                password=hashed_password,
                ip=ip,
                terminal=terminal
            )

            self.db.add(user)
            await self.db.flush()

            return {"ok": True, "message": "User Created successfully", "code": 201, "data": user}

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
        
    async def getUserGeneralData(self, userId: int):
        try:
            result = await self.db.execute(
                select(
                    User.user_id, User.first_name, User.last_name, User.username,
                    User.summary, User.professional_headline, User.avatar, 
                    Country.name.label("country"), User.city, User.created_at
                )
                .select_from(User)
                .outerjoin(Country, and_(Country.country_id == User.country_id, Country.status == "A"))
                .where(and_(User.user_id == userId, User.status == "A"))
            )

            user = result.mappings().first()

            if not user:
                return {"ok": False, "error": "User Not Found", "code": 404}

            user = dict(user)

            return {"ok": True, "message": "User Found", "code": 201, "data": user}
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
        
    async def deleteUserPicture(self, user: User):
        try:
            user.avatar = None
            await self.db.flush()

            return {"ok": True, "message": "Profile Picture Deleted", "code": 201}
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
        
    async def storeUserPicture(self, user: User, filename: str):
        try:
            user.avatar = filename
            await self.db.flush()

            return {"ok": True, "message": "Profile Picture Saved", "code": 201}
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
        
    async def profileUpdate(self, user: User, firstName: str, lastName: str, professionalHeadline: str, summary: str, city: str, countryId: int):
        try:
            user.first_name = firstName
            user.last_name = lastName
            user.professional_headline = professionalHeadline
            user.summary = summary
            user.city = city
            user.country_id = countryId
            await self.db.flush()

            return {"ok": True, "message": "Profile Updated Successfully", "code": 201}
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
        
    async def changePassword(self, user: User, new_password: str):
        try:
            user.password = User.hashPassword(new_password)
            await self.db.flush()

            return {"ok": True, "message": "Password Changed Successfully", "code": 201}
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
