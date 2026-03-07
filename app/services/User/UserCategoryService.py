from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Users.UserCategory import UserCategory
from app.models.General.Category import Category
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy import and_, delete
from app.graphql.UserSkills.UserSkillsPayloads import UserCategoryPayload

class UserCategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def getUserCategories(self, userId):
        try:            
            result = await self.db.execute(
                select(
                    UserCategory.category_id,
                    UserCategory.user_id,
                    Category.name.label("category")
                )
                .join(
                    Category, 
                    and_(
                        UserCategory.category_id == Category.category_id,
                        Category.status == "A"
                    )
                )
                .filter(and_(UserCategory.user_id == userId, UserCategory.status == "A"))
            )

            records = result.mappings().all()

            user_categories_list = [
                UserCategoryPayload(
                    userId = item['user_id'],
                    categoryId = item['category_id'],
                    name = item['category'],
                )
                for item in records
            ]
    
            return {"ok": True, "message": "User Categories", "code": 201, "data": user_categories_list}
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
        
    async def deleteUserCategories(self, userId, categoryIds):
        try:            
            # delete = await self.db.execute(
            #     update(UserCategory)
            #     .where(
            #         and_(
            #             UserCategory.user_id == userId,
            #             UserCategory.category_id.not_in(categoryIds),
            #             UserCategory.status == "A"
            #         )
            #     )
            #     .values(status="I")
            # )
            await self.db.execute(
                delete(UserCategory)
                .where(
                    and_(
                        UserCategory.user_id == userId,
                        UserCategory.category_id.not_in(categoryIds),
                        UserCategory.status == "A"
                    )
                )
            )
            await self.db.flush()
    
            return {"ok": True, "message": "Deleted  User Categories", "code": 201, "data": None}
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
        
    async def deleteAllUserCategories(self, userId):
        try:            
            await self.db.execute(
                delete(UserCategory)
                .where(
                    and_(
                        UserCategory.user_id == userId,
                        UserCategory.status == "A"
                    )
                )
            )
            await self.db.flush()
    
            return {"ok": True, "message": "Deleted All User Categories", "code": 201, "data": None}
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
        
    async def validateUserCategory(self, userId, categoryId):
        try:            
            result = await self.db.execute(
                select(UserCategory)
                .filter(
                    and_(
                        UserCategory.user_id == userId,
                        UserCategory.category_id == categoryId,
                        UserCategory.status == "A"
                    )
                )
            )

            existing_record = result.scalar_one_or_none()

            validation = True if existing_record else False

            return {"ok": True, "message": "Validated User Category", "code": 201, "data": validation}
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
        
    async def storeUserCategories(self, userId, categoryIds, terminal, ip):
        try:
            user_categories_to_add = []
            for category_id in categoryIds: 
                user_categories_to_add.append(
                    UserCategory(
                        user_id=userId,
                        category_id=category_id,
                        ip=ip,
                        terminal=terminal
                    )
                )

            self.db.add_all(user_categories_to_add)
            await self.db.flush()
    
            return {"ok": True, "message": "Stored User Categories", "code": 201, "data": None}
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