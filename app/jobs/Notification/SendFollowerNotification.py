from app.celery.worker import celery_app
from app.db.database import get_pgsql_celery
from app.services.User.UserService import UserService
from app.services.Notification.NotificationService import NotificationService
from app.utils.helpers import Helpers
from strawberry.exceptions import GraphQLError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.config.logger import logger
from app.services.PubSub.RedisPubSub import PubSubManager
import random

@celery_app.task(name="send_follower_notification")
def sendFollowerNotification(followerId, followedId, ip, terminal):
    async def _logic():
        db = get_pgsql_celery()
        
        notification_service = NotificationService(db)
        user_service = UserService(db)
        pubsub_manager = PubSubManager()

        try:
            followerInfo = await user_service.getUserById(userId=followerId)
            if not followerInfo.get("ok", False):
                raise GraphQLError(message=followerInfo['error'], extensions={"code": "BAD_USER_INPUT"})

            followerInfo = followerInfo.get("data")

            title = 'New Follower'
            description = get_random_follower_message(username=followerInfo.username)
            type = "NEW_FOLLOWER"
            avatar = followerInfo.avatar

            stored_notifications = await notification_service.store(emitterId=followerId, receipterId=followedId, type=type, entity='users', entityId=followerId, title=title, description=description, image=avatar, ip=ip, terminal=terminal)
            if not stored_notifications.get('ok', False):
                raise GraphQLError(message=stored_notifications['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
            
            await db.commit()
            
            notification = stored_notifications.get('data')

            await pubsub_manager.publish(
                channel=f"notifications:{followedId}",
                message_data={
                    "notification_id": notification.notification_id,
                    "type": type,
                    "entity_id": followerId,
                    "title": title,
                    "description": description,
                    "is_read": False,
                    "image": avatar
                }
            )

        except GraphQLError as e:
            logger.error(e.message)
            raise e

        except Exception as e:
            logger.exception("Celery notification error")

            await db.rollback()

            error_mapping = {
                IntegrityError: ("BAD_USER_INPUT", "E-mail already in used"),
                SQLAlchemyError: ("INTERNAL_SERVER_ERROR", "Error interno del servidor"),
                ValueError: ("BAD_USER_INPUT", "Datos inválidos"),
                PermissionError: ("FORBIDDEN", "Permiso denegado"),
                FileNotFoundError: ("NOT_FOUND", "Archivo no encontrado"),
                ConnectionError: ("TOO_MANY_REQUESTS", "Demasiadas solicitudes"),
            }

            error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
        
        finally:
            await db.close()

    return Helpers.run_async(_logic())

def get_random_follower_message(username: str) -> str:
    messages = [
        f"{username} is now following you!",
        f"{username} just started following your journey",
        f"You have a new follower: {username}",
        f"{username} joined your followers list",
        f"Hey! {username} is now keeping up with your work",
        f"New connection: {username} is following you"
    ]
    return random.choice(messages)