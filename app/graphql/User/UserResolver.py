import strawberry
from app.config.logger import logger
from app.services.User.UserService import UserService
from app.services.Chat.ChatService import ChatService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.graphql.User.UserInputs import ProfileInput, RegisterInput, StorePictureInput
from app.utils.helpers import Helpers
from app.graphql.Standard.StandardPayloads import ResponsesPayload
from app.graphql.User.UserPayloads import ProfilePayload, UserGeneralDataPayload, UserStatsPayload
from app.jobs.User.MigrateUserMongo import migrateUserMongo
from app.jobs.User.UpdateUserAvatar import updateUserAvatar
from typing import Optional

@strawberry.type
class UserQuery:
    @strawberry.field
    async def getUserGeneralData(self, info, userId: int) -> UserGeneralDataPayload:
        mongo = info.context["mongo_db"]
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)
        chat_service = ChatService(mongo)

        try:
            user = await user_service.getUserGeneralData(userId=userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})

            chat = await chat_service.getChatByUsers(userA=current_user.userId, userB=userId)
            if not chat.get("ok", False):
                raise GraphQLError(message=chat['error'], extensions={"code": "BAD_USER_INPUT"})
            
            user = user.get("data")
            chat = chat.get("data")
            
            return UserGeneralDataPayload(
                userId=user['user_id'], 
                firstName=user['first_name'], 
                lastName=user['last_name'], 
                username=user['username'], 
                professionalHeadline=user['professional_headline'], 
                summary=user['summary'], 
                location=user['country'], 
                city=user['city'], 
                avatar=user['avatar'], 
                since=user['created_at'],
                chatId=chat["chatId"],
                cover=user['cover']
            )
        
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
        
    @strawberry.field
    async def getUserStats(self, info, userId: Optional[int] = None) -> UserStatsPayload:
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)

        try:
            if userId is None:
                userId = current_user.userId

            user_stats = await user_service.getUserStats(userId=userId)
            if not user_stats.get("ok", False):
                raise GraphQLError(message=user_stats['error'], extensions={"code": "BAD_USER_INPUT"})
            
            stats = user_stats.get('data')
           
            return stats

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
class UserMutation:
    @strawberry.mutation
    async def registerUser(self, info, user_data: RegisterInput) -> str:
        db = info.context["db"]
        request = info.context["request"]
        
        user_service = UserService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)

        try:
            verify_email = await user_service.getUserByEmail(email=user_data.email)
            if verify_email.get("ok", True):
                raise GraphQLError(message="Email already in use", extensions={"code": "BAD_USER_INPUT"})
            
            verify_username = await user_service.getUserByUsername(user_data.username)
            if verify_username.get("ok", True):
                raise GraphQLError(message="Username already in use", extensions={"code": "BAD_USER_INPUT"})

            user = await user_service.registerUser(
                user_data.firstName, 
                user_data.lastName, 
                user_data.username, 
                user_data.email, 
                user_data.password,
                ip,
                terminal
            )
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})
            
            await db.commit()

            newUser = user.get("data")
            migrateUserMongo.delay(newUser.user_id, newUser.username, ip, terminal)
            
            return user.get('message')

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
    async def storeUserPicture(self, info, data: StorePictureInput) -> ResponsesPayload:
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)
        
        try:
            user = await user_service.getUserById(userId=current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})

            user = user.get("data")
            fileToDelete = user.avatar if data.type == 'avatar' else user.cover
            
            if fileToDelete:
                delete_picture = await Helpers.deleteFile(filename=fileToDelete, type=data.type)
                if not delete_picture.get("ok", False):
                    raise GraphQLError(message=delete_picture['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})

                delete_previous_picture = await user_service.deleteUserPicture(user=user, type=data.type)
                if not delete_previous_picture.get("ok", False):
                    raise GraphQLError(message=delete_previous_picture['error'], extensions={"code": "BAD_USER_INPUT"})
                
            filename = await Helpers.generateRandomFilename(extension=".jpeg")
            picture_content = await data.picture.read()

            store_picture_server = await Helpers.decodedAndSaveFile(filename=filename, file=picture_content, type=data.type, decode=False)
            if not store_picture_server.get("ok", False):
                raise GraphQLError(message=store_picture_server['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
            
            store_picture_db = await user_service.storeUserPicture(user=user, filename=filename, type=data.type)
            if not store_picture_db.get("ok", False):
                raise GraphQLError(message=store_picture_db['error'], extensions={"code": "BAD_USER_INPUT"})
            
            await db.commit()
            updateUserAvatar.delay(user.user_id, filename)
            
            return ResponsesPayload(label=store_picture_db.get("message"), value=filename)
        
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
    async def profileUpdate(self, info, profile_update: ProfileInput) -> ProfilePayload:
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)
        
        try:
            user = await user_service.getUserById(userId=current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})

            user=user.get("data")
            
            update = await user_service.profileUpdate(
                user,
                profile_update.firstName, 
                profile_update.lastName, 
                profile_update.professionalHeadline,
                profile_update.summary,
                profile_update.city, 
                profile_update.countryId
            )
            if not update.get("ok", False):
                raise GraphQLError(message=update['error'], extensions={"code": "BAD_USER_INPUT"})
            
            await db.commit()

            return ProfilePayload(message=update.get("message"), values=profile_update)
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
    async def changePassword(self, info, currentPassword: str, newPassword: str) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)
        
        try:
            user = await user_service.getUserById(userId=current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})

            user=user.get("data")
            if not user.verifyPassword(currentPassword, user.password):
                raise GraphQLError(message="Invalid Password", extensions={"code": "BAD_USER_INPUT"})
            
            update = await user_service.changePassword(user=user, new_password=newPassword)
            if not update.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})
            
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