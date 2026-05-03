from app.celery.worker import celery_app
from app.db.database import get_pgsql_celery
from app.services.Artwork.ArtworkScheduleService import ArtworkScheduleService
from app.services.Artwork.ArtworkService import ArtworkService
from app.utils.helpers import Helpers
from strawberry.exceptions import GraphQLError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.config.logger import logger

@celery_app.task(name="publish_scheduled_artworks")
def publishScheduledArtworks():
    async def _logic():
        db = get_pgsql_celery()
        
        schedule_service = ArtworkScheduleService(db)
        artwork_service = ArtworkService(db)

        try:
            pending_artworks = await schedule_service.getPendingArtworks()
            if not pending_artworks.get("ok", False):
                raise GraphQLError(message=pending_artworks['error'], extensions={"code": "BAD_USER_INPUT"})
            
            for schedule in pending_artworks.get("data"):
                publish = await artwork_service.publishArtwork(
                    artwork_id=schedule.artwork_id,
                    publishing_id_target=schedule.publishing_id_target
                )
                if not publish.get("ok", False):
                    raise GraphQLError(message=publish['error'], extensions={"code": "BAD_USER_INPUT"})

                mark_published = await schedule_service.markAsPublished(schedule.artwork_schedule_id)
                if not mark_published.get("ok", False):
                    raise GraphQLError(message=mark_published['error'], extensions={"code": "BAD_USER_INPUT"})

                await db.commit()
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

            error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
        
        finally:
            await db.close()

    return Helpers.run_async(_logic())