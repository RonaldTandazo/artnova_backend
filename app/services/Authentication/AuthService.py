from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Users.User import User
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.config.logger import logger
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from app.security.AuthGraph import createAccessToken, createRefreshToken, verifyToken
from datetime import timedelta
from app.models.Auth.RefreshToken import RefreshToken
import datetime
from app.utils.helpers import Helpers

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def loginUser(self, username: str, password: str, rememberMe: bool):
        try:
            result = await self.db.execute(
                select(User)
                .options(joinedload(User.country))
                .filter(and_(User.username == username, User.status == "A"))
            )

            user = result.scalar_one_or_none()
            
            if user:
                if User.verifyPassword(password, user.password):
                    if user.country != None:
                        user.country_name = user.country.name

                    accessTokenData = await Helpers.prepareAccessTokenData(user)
                    accessToken = createAccessToken(data=accessTokenData)

                    if rememberMe:
                        refreshToken = createRefreshToken(data={
                            "sub": str(user.user_id),
                            "rememberMe": rememberMe
                        })
                    else:
                        refreshToken = createRefreshToken(
                            data={
                                "sub": str(user.user_id),
                                "rememberMe": rememberMe
                            },
                            expires_delta=timedelta(hours=1)
                        )

                    new_refresh_token = RefreshToken(
                        user_id=user.user_id,
                        token=refreshToken['token'],
                        expires_at=refreshToken['expire_at']
                    )
                    self.db.add(new_refresh_token)
                    await self.db.flush()

                    tokensData = {
                        "accessToken":accessToken,
                        "refreshToken":refreshToken['token']
                    }

                    return {"ok": True, "message": "Sign In Success", "code": 201, "data": tokensData}
    
                return {"ok": False, "error": "Invalid Credentials", "code": 400}

            return {"ok": False, "error": "Invalid Credentials", "code": 404}
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
        
    async def refreshTokens(self, current_refresh_token: str):
        try:
            payload = verifyToken(current_refresh_token)
            user_id = payload.get("sub")
            rememberMe = payload.get("rememberMe")
            if user_id is None:
                raise ValueError("Invalid refresh token payload")

            result = await self.db.execute(
                select(RefreshToken).filter(
                    and_(
                        RefreshToken.token == current_refresh_token,
                        RefreshToken.user_id == int(user_id),
                        RefreshToken.expires_at > datetime.datetime.now(),
                        RefreshToken.is_revoked == False
                    )
                )
            )
            db_refresh_token = result.scalar_one_or_none()

            if not db_refresh_token:
                raise PermissionError("Invalid or revoked refresh token")

            db_refresh_token.is_revoked = True
            await self.db.flush()

            user_result = await self.db.execute(
                select(User)
                .options(joinedload(User.country))
                .filter(User.user_id == int(user_id))
            )
            user = user_result.scalar_one_or_none()

            if not user:
                raise ValueError("User not found for refresh token")

            access_token_data = await Helpers.prepareAccessTokenData(user)

            new_access_token = createAccessToken(data=access_token_data)
            
            if rememberMe:
                new_refresh_token = createRefreshToken(data={
                    "sub": str(user.user_id),
                    "rememberMe": rememberMe
                })
            else:
                new_refresh_token = createRefreshToken(
                    data={
                        "sub": str(user.user_id),
                        "rememberMe": rememberMe
                    },
                    expires_delta=timedelta(hours=1)
                )

            refresh_token_store = RefreshToken(
                user_id=int(user.user_id),
                token=new_refresh_token['token'],
                expires_at=new_refresh_token['expire_at']
            )

            self.db.add(refresh_token_store)
            await self.db.flush()

            new_tokens = {
                "accessToken": new_access_token,
                "refreshToken": new_refresh_token['token']
            }
            
            return {"ok": True, "message": "Tokens Refreshed", "code": 201, "data": new_tokens}
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
    
    async def revokeToken(self, token: str):
        try:
            payload = verifyToken(token, origin = 'Revoke')
            user_id = payload.get("sub")
            if user_id is None:
                raise ValueError("Invalid refresh token payload")
            
            result = await self.db.execute(
                select(RefreshToken).filter(
                    and_(
                        RefreshToken.token == token,
                        RefreshToken.user_id == int(user_id),
                        # RefreshToken.expires_at > datetime.datetime.now(),
                        RefreshToken.is_revoked == False
                    )
                )
            )
            db_refresh_token = result.scalar_one_or_none()

            if not db_refresh_token:
                raise PermissionError("Invalid or revoked refresh token")

            db_refresh_token.is_revoked = True
            await self.db.flush()

            return {"ok": True, "message": "Token Revoked Successfully", "code": 201, "data": None}
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