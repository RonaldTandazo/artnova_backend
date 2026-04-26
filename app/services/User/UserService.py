from app.config.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc, or_, func
from sqlalchemy.future import select
from typing import Any
from app.models.Users.User import User
from app.models.General.Country import Country
from app.models.Follows.Follow import Follow
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.graphql.User.UserPayloads import ArtistPayload, UserStatsPayload

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
                    User.summary, User.professional_headline, User.avatar, User.cover,
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
        
    async def getUserStats(self, userId: int):
        try:
            followers_stmt = (
                select(func.count(Follow.follow_id))
                .where(and_(Follow.followed_id == userId, Follow.status == "A"))
                .scalar_subquery()
            )

            following_stmt = (
                select(func.count(Follow.follow_id))
                .where(and_(Follow.follower_id == userId, Follow.status == "A"))
                .scalar_subquery()
            )

            result = await self.db.execute(
                select(
                    followers_stmt.label("followersCount"),
                    following_stmt.label("followingCount")
                )
            )
            
            row = result.mappings().first()

            stats = UserStatsPayload(
                followersCount=row["followersCount"] if row else 0,
                followingCount=row["followingCount"] if row else 0,
            )

            return {"ok": True, "message": "User Stats Got", "code": 201, "data": stats}
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
        
    async def deleteUserPicture(self, user: User, type: str):
        try:
            if type == 'avatar':
                user.avatar = None

            if type == 'cover':
                user.cover = None
            
            await self.db.flush()

            return {"ok": True, "message": "Picture Deleted", "code": 201}
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
        
    async def storeUserPicture(self, user: User, filename: str, type: str):
        try:
            if type == 'avatar':
                user.avatar = filename
            
            if type == 'cover':
                user.cover = filename
            
            await self.db.flush()

            return {"ok": True, "message": "Picture Stored", "code": 201}
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
        
    async def getArtistsBySearch(self, search: str, page: int = 1, page_size: int = 20, blockerIds: list[int] = []):
        try:
            query = select(
                User.user_id.label("user_id"),
                User.username.label("username"),
                User.avatar.label("avatar"),
                User.cover.label("cover")
            ).where(and_(User.status == "A", User.user_id.not_in(blockerIds)))

            if search:
                terms = search.strip().split()
                if terms:
                    all_conditions = []

                    for term in terms:
                        search_pattern = f"%{term.strip()}%"
                        all_conditions.append(or_(
                            User.username.ilike(search_pattern)
                        ))

                    query = query.where(or_(*all_conditions))

            offset = (page - 1) * page_size
            query = query.order_by(desc(User.created_at)).limit(page_size + 1).offset(offset)

            result = await self.db.execute(query)
            rows = result.mappings().all()

            has_more = len(rows) > page_size
            data_rows = rows[:page_size]

            artists = [
                ArtistPayload(
                    artistId=artist['user_id'],
                    username=artist['username'],
                    avatar=artist['avatar'],
                    cover=artist['cover'],
                ) for artist in data_rows
            ]

            data = {
                'artists': artists,
                'hasMore': has_more
            }

            return {"ok": True, "message": "Artists Found", "code": 201, "data": data}
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
