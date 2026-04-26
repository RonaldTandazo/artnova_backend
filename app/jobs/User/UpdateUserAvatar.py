from app.celery.worker import celery_app
from app.db.database import get_mongo_celery, get_pgsql_celery
from app.utils.helpers import Helpers
from app.config.logger import logger
from strawberry.exceptions import GraphQLError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.services.Notification.NotificationService import NotificationService

@celery_app.task(name="update_user_avatar")
def updateUserAvatar(user_id, filename):
    async def _logic():
        mongo_db = get_mongo_celery()
        pgsql = get_pgsql_celery()

        notification_service = NotificationService(pgsql)

        try:
            collection = mongo_db.get_collection("artwork_statistics")

            await collection.update_many(
                {"comments.user_id": user_id},
                {
                    "$set": {
                        "comments.$[comment].avatar": filename
                    }
                },
                array_filters=[{"comment.user_id": user_id}]
            )

            update_notification_image = await notification_service.updateNotificationImage(entityId=user_id, entity='users', image=filename)
            if not update_notification_image.get('ok', False):
                raise GraphQLError(message=update_notification_image['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
            
            await pgsql.commit()
        except GraphQLError as e:
            logger.error(e.message)
            raise e

        except Exception as e:
            await pgsql.rollback()

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
            await pgsql.close()

    Helpers.run_async(_logic())