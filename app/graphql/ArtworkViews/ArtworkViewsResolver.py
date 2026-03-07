import strawberry
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.utils.helpers import Helpers
from app.services.ArtworkViews.ArtworkViewsService import ArtworkViewsService
from app.services.ArtworkStatistics.ArtworkStatisticsService import ArtworkStatisticsService

@strawberry.type
class ArtworkViewsMutation:
    @strawberry.mutation
    async def storeArtworkViews(self, info, artworkId: int) -> str:
        db = info.context["mongo_db"]
        current_user = info.context["current_user"]
        request = info.context["request"]

        awk_vws_service = ArtworkViewsService(db)
        awk_stts_service = ArtworkStatisticsService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)
        try:
            userId = None
            if current_user:
                userId = current_user.userId

            verify_existance = await awk_vws_service.verifyExistance(artworkId=artworkId, userId=userId, ip=ip)
            if not verify_existance.get("ok", False):
                raise GraphQLError(message=verify_existance['error'], extensions={"code": "BAD_USER_INPUT"})
            
            data = verify_existance.get("data")

            if not data["exists"]:
                update_views_stats = await awk_stts_service.updateArtworkViews(artworkId=artworkId)
                if not update_views_stats.get("ok", False):
                    raise GraphQLError(message=update_views_stats['error'], extensions={"code": "BAD_USER_INPUT"})

                new_document = await awk_vws_service.store(artworkId=artworkId, userId=userId, ip=ip, terminal=terminal)
                if not new_document.get("ok", False):
                    raise GraphQLError(message=new_document['error'], extensions={"code": "BAD_USER_INPUT"})
            
            return 'Artwork View Succesfully Stored'

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