from app.celery.worker import celery_app
from app.db.database import get_pgsql_celery
from app.services.Artwork.ArtworkUserFavoriteService import ArtworkUserFavoriteService
from app.utils.helpers import Helpers
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError

@celery_app.task(name="migrate_user_favorite_artworks")
def migrateUserFavoriteArtworks(userId, artworkId, isFavorite, ip, terminal):
    async def _logic():
        db = get_pgsql_celery()
        
        favorite_service = ArtworkUserFavoriteService(db)

        try:
            if isFavorite:
                store = await favorite_service.store(artworkId=artworkId, userId=userId, ip=ip, terminal=terminal)
                if not store.get("ok", False):
                    raise GraphQLError(message=store['error'], extensions={"code": "BAD_USER_INPUT"})
                
            else:
                delete = await favorite_service.deleteByUserAndArtWork(artworkId=artworkId, userId=userId)
                if not delete.get("ok", False):
                    raise GraphQLError(message=delete['error'], extensions={"code": "BAD_USER_INPUT"})

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