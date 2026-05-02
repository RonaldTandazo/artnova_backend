import strawberry
from app.services.Authentication.AuthService import AuthService
from app.config.logger import logger
from strawberry.exceptions import GraphQLError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.graphql.Authentication.AuthInputs import ValidateAccessInput
from app.graphql.Authentication.AuthPayloads import AuthPayload, ValidateUserPayload
from app.services.Artwork.ArtworkOwnerService import ArtworkOwnerService
from app.services.User.UserService import UserService

@strawberry.type
class AuthQuery:
    @strawberry.field
    async def validateUserAccess(self, info, data: ValidateAccessInput) -> ValidateUserPayload:
        db = info.context["db"]
        current_user = info.context["current_user"]

        awk_owner_service = ArtworkOwnerService(db)
        awk_usr_service = UserService(db)

        try:
            if data.module in ['OwnProfile', 'ProfileSettings', 'NewArtwork', 'Chats', 'Favorites']:
                if current_user is None or (current_user is not None and current_user.userId != data.value):
                    return ValidateUserPayload(validate=False)
                
            elif data.module == 'VisitProfile':
                validation = await awk_usr_service.getUserById(userId=data.value)
                if not validation.get('ok', False):
                    return ValidateUserPayload(validate=False)
            
            elif data.module == 'ArtWorkEdit':
                artworkIds = data.value if isinstance(data.value, list) else [data.value]

                validation = await awk_owner_service.validateArtworksOwner(userId=current_user.userId, ArtworkIds=artworkIds)
                if not validation.get('ok', False):
                    return ValidateUserPayload(validate=False)
                
                result = validation.get('data')
                all_valid = result['all_valid']

                if not all_valid:
                    return ValidateUserPayload(validate=False)
            
            else:
                return ValidateUserPayload(validate=False)
                
            return ValidateUserPayload(validate=True)
        
        except GraphQLError as e:
            logger.error(e.message)
            raise e
        
        except Exception as e:
            error_mapping = {
                IntegrityError: ("BAD_USER_INPUT", "E-mail already in used"),
                SQLAlchemyError: ("INTERNAL_SERVER_ERROR", "Error interno del servidor"),
                ValueError: ("BAD_USER_INPUT", "Datos inválidos"),
                PermissionError: ("FORBIDDEN", "Permiso denegado"),
                FileNotFoundError: ("NOT_FOUND", "Archivo no encontrado"),
                ConnectionError: ("TOO_MANY_REQUESTS", "Demasiadas solicitudes"),
            }

            extension_code, error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
            raise GraphQLError(message=error_message, extensions={"code": extension_code})

@strawberry.type
class AuthMutation:
    @strawberry.mutation
    async def login(self, info, username: str, password: str, rememberMe: bool) -> AuthPayload:
        db = info.context["db"]
        auth_service = AuthService(db)

        try:
            login = await auth_service.loginUser(username=username, password=password, rememberMe=rememberMe)
            if not login.get("ok", False):
                raise GraphQLError(message=login['error'], extensions={"code": "BAD_USER_INPUT"})
            
            loginData = login.get("data")
            accessToken = loginData['accessToken']
            refreshToken = loginData['refreshToken']
            
            await db.commit()
            
            return AuthPayload(accessToken=accessToken, refreshToken=refreshToken, tokenType="bearer")

        except GraphQLError as e:
            logger.error(e.message)
            raise e

        except Exception as e:
            await db.rollback()

            error_mapping = {
                IntegrityError: ("BAD_USER_INPUT", "E-mail already in used"),
                SQLAlchemyError: ("INTERNAL_SERVER_ERROR", "Error interno del servidor"),
                ValueError: ("BAD_USER_INPUT", "Datos inválidos"),
                PermissionError: ("FORBIDDEN", "Permiso denegado"),
                FileNotFoundError: ("NOT_FOUND", "Archivo no encontrado"),
                ConnectionError: ("TOO_MANY_REQUESTS", "Demasiadas solicitudes"),
            }

            extension_code, error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
            raise GraphQLError(message=error_message, extensions={"code": extension_code})
        
    @strawberry.mutation
    async def refreshToken(self, info, refreshToken: str) -> AuthPayload:
        db = info.context["db"]
        auth_service = AuthService(db)

        try:
            tokens = await auth_service.refreshTokens(current_refresh_token=refreshToken)
            if not tokens.get("ok", False):
                raise GraphQLError(message="Token refresh failed", extensions={"code": "UNAUTHENTICATED"})
            
            tokensData = tokens.get("data")
            
            accessToken = tokensData['accessToken']
            refreshToken = tokensData['refreshToken']
            
            await db.commit()

            return AuthPayload(accessToken=accessToken, refreshToken=refreshToken, tokenType="bearer")
        
        except GraphQLError as e:
            logger.error(e.message)
            raise e
        
        except Exception as e:
            await db.rollback()
            
            logger.error(e)
            raise GraphQLError(message="Could not refresh token", extensions={"code": "INTERNAL_SERVER_ERROR"})
        
    @strawberry.mutation
    async def revokeToken(self, info, refreshToken: str) -> str:
        db = info.context["db"]
        auth_service = AuthService(db)

        try:
            revoke = await auth_service.revokeToken(token=refreshToken)
            if not revoke.get("ok", False):
                raise GraphQLError(message="Token revoke failed", extensions={"code": "UNAUTHENTICATED"})
            
            await db.commit()

            return revoke.get("message")
        except GraphQLError as e:
            logger.error(e.message)
            raise e
        except Exception as e:
            await db.rollback()
            logger.error(e)
            raise GraphQLError(message="Could not refresh token", extensions={"code": "INTERNAL_SERVER_ERROR"})