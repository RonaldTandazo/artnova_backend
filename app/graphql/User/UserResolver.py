import strawberry
from app.config.logger import logger
from app.services.User.UserService import UserService
from app.services.Chat.ChatService import ChatService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.graphql.User.UserInputs import ProfileInput, RegisterInput
from app.utils.helpers import Helpers
from app.graphql.Standard.StandardPayloads import ResponsesPayload
from strawberry.file_uploads import Upload
from app.graphql.User.UserPayloads import ProfilePayload, UserGeneralDataPayload
from app.jobs.User.MigrateUserMongo import migrateUserMongo
from app.jobs.User.UpdateUserAvatarMongo import updateAvatarMongo

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
                chatId=chat["chatId"]
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
    async def storeUserPicture(self, info, picture: Upload) -> ResponsesPayload:
        db = info.context["db"]
        current_user = info.context["current_user"]

        user_service = UserService(db)
        
        try:
            user = await user_service.getUserById(userId=current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})

            user = user.get("data")
            if user.avatar:
                delete_avatar = await Helpers.deleteFile(filename=user.avatar, type="avatar")
                if not delete_avatar.get("ok", False):
                    raise GraphQLError(message=delete_avatar['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})

                delete_previous_picture = await user_service.deleteUserPicture(user=user)
                if not delete_previous_picture.get("ok", False):
                    raise GraphQLError(message=delete_previous_picture['error'], extensions={"code": "BAD_USER_INPUT"})
                
            filename = await Helpers.generateRandomFilename(extension=".jpeg")
            picture_content = await picture.read()

            avatar_store = await Helpers.decodedAndSaveFile(filename=filename, file=picture_content, type="avatar", decode=False)
            if not avatar_store.get("ok", False):
                raise GraphQLError(message=avatar_store['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
            
            store_avatar = await user_service.storeUserPicture(user=user, filename=filename)
            if not store_avatar.get("ok", False):
                raise GraphQLError(message=store_avatar['error'], extensions={"code": "BAD_USER_INPUT"})
            
            await db.commit()
            updateAvatarMongo.delay(user.user_id, filename)
            
            return ResponsesPayload(label=store_avatar.get("message"), value=filename)
        
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