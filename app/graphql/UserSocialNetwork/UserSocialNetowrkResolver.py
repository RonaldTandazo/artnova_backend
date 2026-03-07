import strawberry
from app.config.logger import logger
from app.services.User.UserService import UserService
from app.services.User.UserSocialNetworkService import UserSocialNetworkService 
from app.utils.helpers import Helpers
from app.graphql.UserSocialNetwork.UserSocialNetworkInputs import SocialMediaStoreInput, UpdateUserNetworkInput
from app.graphql.UserSocialNetwork.UserSocialNetworkPayloads import SocialMediPayload
from app.graphql.User.UserInputs import UserVariablesInput
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError

@strawberry.type
class UserSocialNetworkQuery:
    @strawberry.field
    async def getUserSocialMedia(self, info, data: UserVariablesInput) -> list[SocialMediPayload]:
        db = info.context["db"]
        current_user = info.context["current_user"]

        usr_scl_ntw_service = UserSocialNetworkService(db)
        
        try:
            userId = current_user.userId
            if data.module == 'VisitProfile':
                userId = data.userId

            social_media = await usr_scl_ntw_service.getUserSocialMedia(userId=userId)
            if not social_media.get("ok", False):
                raise GraphQLError(message=social_media['error'], extensions={"code": "BAD_USER_INPUT"})
            
            social_media = social_media.get("data")

            return [SocialMediPayload(userSocialNetworkId=item['user_social_network_id'], socialMediaId=item['social_media_id'], network=item['network_name'], link=item['link']) for item in social_media]
        
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
class UserSocialNetworkMutation:
    @strawberry.mutation
    async def storeUserSocialNetwork(self, info, storeUserNetwork: SocialMediaStoreInput) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]
        request = info.context["request"]
        
        user_service = UserService(db)
        usr_scl_ntw_service = UserSocialNetworkService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)

        try:
            user = await user_service.getUserById(userId=current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})

            store = await usr_scl_ntw_service.store(
                current_user.userId,
                storeUserNetwork.socialMediaId, 
                storeUserNetwork.link,
                ip,
                terminal
            )
            if not store.get("ok", False):
                raise GraphQLError(message=store['error'], extensions={"code": "BAD_USER_INPUT"})
            
            await db.commit()

            return store.get("message")

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
    async def updateUserSocialNetwork(self, info, updateUserNetwork: UpdateUserNetworkInput) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)
        usr_scl_ntw_service = UserSocialNetworkService(db)

        try:
            user = await user_service.getUserById(userId=current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})

            item = await usr_scl_ntw_service.getUserSocialMediaById(updateUserNetwork.userSocialNetworkId)
            if not item.get("ok", False):
                raise GraphQLError(message=item['error'], extensions={"code": "BAD_USER_INPUT"})
            
            item = item.get("data")

            update = await usr_scl_ntw_service.update(
                item,
                updateUserNetwork.socialMediaId,
                updateUserNetwork.link
            )
            if not update.get("ok", False):
                raise GraphQLError(message=update['error'], extensions={"code": "BAD_USER_INPUT"})

            await db.commit()
            
            return update.get("message")

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
    async def removeUserSocialNetwork(self, info, userSocialNetworkId: int) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)
        usr_scl_ntw_service = UserSocialNetworkService(db)
        
        try:
            user = await user_service.getUserById(userId=current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})
            
            item = await usr_scl_ntw_service.getUserSocialMediaById(userSocialNetworkId)
            if not item.get("ok", False):
                raise GraphQLError(message=item['error'], extensions={"code": "BAD_USER_INPUT"})
            
            item = item.get("data")

            remove = await usr_scl_ntw_service.remove(
                item
            )

            if not remove.get("ok", False):
                raise GraphQLError(message=remove['error'], extensions={"code": "BAD_USER_INPUT"})
            
            await db.commit()
                
            return remove.get("message")

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
        

