import strawberry
from app.config.logger import logger
from typing import AsyncGenerator
from app.services.PubSub.RedisPubSub import PubSubManager
from app.graphql.Notifications.NotificationPayloads import NotificationPayload, UserNotifications
from app.graphql.Notifications.NotificationInputs import UserNotificationsInput, MarkNotificationAsReadInput
from app.services.Notification.NotificationService import NotificationService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError

@strawberry.type
class NotificationQuery:
    @strawberry.field
    async def getUserNotifications(self, info, input: UserNotificationsInput) -> UserNotifications:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        notification_service = NotificationService(db)

        try:
            unread_notifications = await notification_service.getUserUnreadNotifications(userId=current_user.userId)
            if not unread_notifications.get("ok", False):
                raise GraphQLError(message=unread_notifications['error'], extensions={"code": "NOT_FOUND"})

            notifications = await notification_service.getUserNotifications(userId=current_user.userId, page=input.page)
            if not notifications.get("ok", False):
                raise GraphQLError(message=notifications['error'], extensions={"code": "NOT_FOUND"})
            
            notifications = notifications.get("data")
            unread_notifications = unread_notifications.get("data")

            return UserNotifications(
                notifications = notifications['notifications'],
                unreadNotifications = unread_notifications,
                hasMore = notifications['hasMore']
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
class NotificationMutation:
    @strawberry.mutation
    async def markAllAsRead(self, info) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]

        notification_service = NotificationService(db)

        try:
            mark_all_read = await notification_service.markAllAsRead(userId=current_user.userId)
            if not mark_all_read.get("ok", False):
                raise GraphQLError(message=mark_all_read['error'], extensions={"code": "NOT_FOUND"})
            
            await db.commit()

            return mark_all_read.get('message')
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
        
    @strawberry.mutation
    async def markNotificationAsRead(self, info, input: MarkNotificationAsReadInput) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]

        notification_service = NotificationService(db)

        try:
            mark_as_read = await notification_service.markNotificationAsRead(notificationId=input.notificationId, userId=current_user.userId)
            if not mark_as_read.get("ok", False):
                raise GraphQLError(message=mark_as_read['error'], extensions={"code": "NOT_FOUND"})
            
            await db.commit()

            return mark_as_read.get('message')
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
class NotificationSubscription:
    @strawberry.subscription
    async def notificationReceived(self, info, userId: int) -> AsyncGenerator[NotificationPayload, None]:

        pubsub_manager = PubSubManager()
        channel = f"notifications:{userId}"

        async for message_data in pubsub_manager.subscribe(channel):
            yield NotificationPayload(
                notificationId=message_data["notification_id"],
                type=message_data["type"],
                entityId=message_data["entity_id"],
                title=message_data["title"],
                description=message_data["description"],
                isRead=message_data["is_read"],
                image=message_data["image"]
            )