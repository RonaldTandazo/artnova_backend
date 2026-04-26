from app.celery.worker import celery_app
from app.db.database import get_pgsql_celery, get_mongo_celery
from app.services.Artwork.ArtworkUserFavoriteService import ArtworkUserFavoriteService
from app.services.Artwork.ArtworkService import ArtworkService
from app.services.Artwork.ArtworkOwnerService import ArtworkOwnerService
from app.services.Artwork.ArtworkThumbnailService import ArtworkThumbnailService
from app.services.Artwork.ArtworkCategoryService import ArtworkCategoryService
from app.services.Artwork.ArtworkSoftwareService import ArtworkSoftwareService
from app.services.Artwork.ArtworkTopicService import ArtworkTopicService
from app.services.Artwork.ArtworkImageService import ArtworkImageService
from app.services.Artwork.ArtworkVideoService import ArtworkVideoService
from app.services.ArtworkStatistics.ArtworkStatisticsService import ArtworkStatisticsService
from app.services.ArtworkViews.ArtworkViewsService import ArtworkViewsService
from app.services.Artwork.ArtworkScheduleService import ArtworkScheduleService
from app.utils.helpers import Helpers
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError

@celery_app.task(name="delete_artworks_records")
def deleteArtworksRecords(artworkIds):
    async def _logic():
        pgsql = get_pgsql_celery()
        mongo_db = get_mongo_celery()
        
        awk_service = ArtworkService(pgsql)
        awk_owner_service = ArtworkOwnerService(pgsql)
        awk_thmb_service = ArtworkThumbnailService(pgsql)
        awk_ctg_service = ArtworkCategoryService(pgsql)
        awk_sfw_service = ArtworkSoftwareService(pgsql)
        awk_tpc_service = ArtworkTopicService(pgsql)
        awk_img_service = ArtworkImageService(pgsql)
        awk_vid_service = ArtworkVideoService(pgsql)
        awk_fav_service = ArtworkUserFavoriteService(pgsql)
        awk_sch_service = ArtworkScheduleService(pgsql)
        awk_stats_service = ArtworkStatisticsService(mongo_db)
        awk_views_service = ArtworkViewsService(mongo_db)

        try:
            deleteThumbnails = await awk_thmb_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteThumbnails.get("ok", False):
                raise GraphQLError(message=deleteThumbnails['error'], extensions={"code": "BAD_USER_INPUT"})
                        
            deleteCategories = await awk_ctg_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteCategories.get("ok", False):
                raise GraphQLError(message=deleteCategories['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteSoftwares = await awk_sfw_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteSoftwares.get("ok", False):
                raise GraphQLError(message=deleteSoftwares['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteTopics = await awk_tpc_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteTopics.get("ok", False):
                raise GraphQLError(message=deleteTopics['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteImages = await awk_img_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteImages.get("ok", False):
                raise GraphQLError(message=deleteImages['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteVideos = await awk_vid_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteVideos.get("ok", False):
                raise GraphQLError(message=deleteVideos['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteFavorites = await awk_fav_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteFavorites.get("ok", False):
                raise GraphQLError(message=deleteFavorites['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteViews = await awk_views_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteViews.get("ok", False):
                raise GraphQLError(message=deleteViews['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteStats = await awk_stats_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteStats.get("ok", False):
                raise GraphQLError(message=deleteStats['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteSchedule = await awk_sch_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteSchedule.get("ok", False):
                raise GraphQLError(message=deleteSchedule['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteOwner = await awk_owner_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteOwner.get("ok", False):
                raise GraphQLError(message=deleteOwner['error'], extensions={"code": "BAD_USER_INPUT"})
            
            deleteArtWorks = await awk_service.deleteByArtWorks(artworkIds=artworkIds)
            if not deleteArtWorks.get("ok", False):
                raise GraphQLError(message=deleteArtWorks['error'], extensions={"code": "BAD_USER_INPUT"})
            
            filesToDelete = {
                "thumbnail": deleteThumbnails.get('data', []),
                "image": deleteImages.get('data', []),
                "video": deleteVideos.get('data', [])
            }

            for type, files in filesToDelete.items():
                if files:
                    for filename in files:  
                        await Helpers.deleteFile(filename=filename, type=type)
            
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