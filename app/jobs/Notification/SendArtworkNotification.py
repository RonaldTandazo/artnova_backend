from app.celery.worker import celery_app
from app.db.database import get_pgsql_celery
from app.services.Follow.FollowService import FollowService
from app.services.Notification.NotificationService import NotificationService
from app.utils.helpers import Helpers
from strawberry.exceptions import GraphQLError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.config.logger import logger
from app.services.PubSub.RedisPubSub import PubSubManager
import random

@celery_app.task(name="send_artwork_notification")
def sendArtworkNotification(artistId, artist, artworkId, thumbnail, ip, terminal):
    async def _logic():
        db = get_pgsql_celery()
        
        follow_service = FollowService(db)
        notification_service = NotificationService(db)
        pubsub_manager = PubSubManager()

        try:
            artists_followers = await follow_service.getArtistFollowers(artistId=artistId)
            if not artists_followers.get('ok', False):
                raise GraphQLError(message=artists_followers['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
            
            followers = artists_followers.get('data')

            title = 'New ArtWork'
            description = get_random_artwork_message(artist_name=artist)
            type = "NEW_ARTWORK"

            notifications = []

            for follower in followers:
                if follower['follower_id'] == artistId:
                    continue

                notifications.append({
                    "emitter_id": artistId,
                    "receipter_id": follower['follower_id'],
                    "type": type,
                    "entity": "artworks",
                    "entity_id": artworkId,
                    "title": title,
                    "description": description,
                    "image": thumbnail,
                    "ip": ip,
                    "terminal": terminal
                })

            stored_notifications = await notification_service.bulk_store(notifications=notifications)
            if not stored_notifications.get('ok', False):
                raise GraphQLError(message=stored_notifications['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
            
            await db.commit()
            
            records = stored_notifications.get('data')

            for notification in records:
                await pubsub_manager.publish(
                    channel=f"notifications:{notification['receipter_id']}",
                    message_data={
                        "notification_id": notification["notification_id"],
                        "type": type,
                        "entity_id": artworkId,
                        "title": title,
                        "description": description,
                        "is_read": False,
                        "image": thumbnail
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

    Helpers.run_async(_logic())

def get_random_artwork_message(artist_name: str) -> str:
    messages = [
        f"Check out the new artwork by {artist_name}!",
        f"{artist_name} just published an amazing new piece",
        f"New art drop from {artist_name}! See what's new",
        f"{artist_name} added something new to their gallery",
        f"Fresh art from {artist_name} is now live!",
        f"Don't miss the latest work by {artist_name}"
    ]
    return random.choice(messages)