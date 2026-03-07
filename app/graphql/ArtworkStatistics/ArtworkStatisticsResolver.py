import strawberry
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.utils.helpers import Helpers
from app.graphql.ArtworkStatistics.ArtworkStatisticsInputs import PostCommentInput, DeleteCommentInput, UpdateArtworkLikesInput, UpdateArtworkDisLikesInput, UpdateCommentLikesInput, UpdateCommentDisLikesInput, UpdateArtworkFavoritesInput
from app.graphql.ArtworkStatistics.ArtworkStatisticsPayloads import ArtworkStatisticsPayload, ArtworkCommentPayload, ArtworkStatsPayload
from app.services.ArtworkStatistics.ArtworkStatisticsService import ArtworkStatisticsService
from app.models.ArtworkStatistics.ArtworkComment import ArtworkComment
from app.jobs.Artwork.MigrateUserFavoriteArtworks import migrateUserFavoriteArtworks

@strawberry.type
class ArtworkStatisticsQuery:
    @strawberry.field
    async def getArtworkStatistics(self, info, artworkId: int) -> ArtworkStatisticsPayload:
        db = info.context["mongo_db"]
        awk_stts_service = ArtworkStatisticsService(db)
        try:
            artwork_statistics= await awk_stts_service.getArtworkStatistics(artworkId)
            if not artwork_statistics.get("ok", False):
                raise GraphQLError(message=artwork_statistics['error'], extensions={"code": "NOT_FOUND"})
            
            artwork_statistics = artwork_statistics.get("data")
            artwork_stats = artwork_statistics['stats'] if artwork_statistics else {"views_amount": 0, "likes": [], "dislikes": [], "favorites": [], "comments_amount": 0}
            artwork_comments = artwork_statistics['comments'] if artwork_statistics else []

            stats = ArtworkStatsPayload(viewsAmount=artwork_stats['views_amount'], likes=artwork_stats['likes'], dislikes=artwork_stats['dislikes'], favorites=artwork_stats['favorites'], commentsAmount=artwork_stats['comments_amount'])
            comments = [ArtworkCommentPayload(commentId=comment['commentId'], userId=comment['userId'], username=comment['username'], avatar=comment['avatar'], comment=comment['comment'], likes=comment['likes'], dislikes=comment['dislikes'], replies=comment['replies'], createdAt=comment['createdAt']) for comment in artwork_comments]

            return ArtworkStatisticsPayload(stats=stats, comments=comments)
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
class ArtworkStatisticsMutation:    
    @strawberry.mutation
    async def postArtworkComment(self, info, postCommentData: PostCommentInput) -> str:
        db = info.context["mongo_db"]
        current_user = info.context["current_user"]
        request = info.context["request"]

        awk_stts_service = ArtworkStatisticsService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)
        try:
            verify_existance = await awk_stts_service.verifyExistance(artworkId=postCommentData.artworkId)
            if not verify_existance.get("ok", False):
                raise GraphQLError(message=verify_existance['error'], extensions={"code": "BAD_USER_INPUT"})

            data = verify_existance.get("data")
            if data["exists"]:
                document_id = data['id']

            comment_data = ArtworkComment(
                user_id=current_user.userId, 
                username=current_user.username,
                avatar=postCommentData.avatar,
                comment=postCommentData.comment,
                ip=ip,
                terminal=terminal,
            )

            store_comment = await awk_stts_service.addComment(documentId=document_id, comment_data=comment_data)
            if not store_comment.get("ok", False):
                raise GraphQLError(message=store_comment['error'], extensions={"code": "BAD_USER_INPUT"})

            return store_comment.get("message")

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
    async def deleteArtworkComment(self, info, deleteCommentData: DeleteCommentInput) -> str:
        db = info.context["mongo_db"]
        current_user = info.context["current_user"]
        awk_stts_service = ArtworkStatisticsService(db)

        try:
            verify_existance = await awk_stts_service.verifyExistance(deleteCommentData.artworkId)
            if not verify_existance.get("ok", False):
                raise GraphQLError(message=verify_existance['error'], extensions={"code": "BAD_USER_INPUT"})

            data = verify_existance.get("data")
            if data["exists"]:
                document_id = data['id']

            delete_comment = await awk_stts_service.deleteComments(documentId=document_id, commentIds=deleteCommentData.commentIds, userId=current_user.userId)
            if not delete_comment.get("ok", False):
                raise GraphQLError(message=delete_comment['error'], extensions={"code": "BAD_USER_INPUT"})

            return delete_comment.get("message")

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
    async def updateArtworkLikes(self, info, updateArtworkLikesData: UpdateArtworkLikesInput) -> str:
        db = info.context["mongo_db"]
        awk_stts_service = ArtworkStatisticsService(db)        
        try:
            update_likes = await awk_stts_service.updateArtworkLikes(updateArtworkLikesData.artworkId, updateArtworkLikesData.likes)
            if not update_likes.get("ok", False):
                raise GraphQLError(message=update_likes['error'], extensions={"code": "BAD_USER_INPUT"})

            return update_likes.get("message")

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
    async def updateArtworkDisLikes(self, info, updateArtworkDisLikesData: UpdateArtworkDisLikesInput) -> str:
        db = info.context["mongo_db"]
        awk_stts_service = ArtworkStatisticsService(db)        
        try:
            update_dislikes = await awk_stts_service.updateArtworkDisLikes(updateArtworkDisLikesData.artworkId, updateArtworkDisLikesData.dislikes)
            if not update_dislikes.get("ok", False):
                raise GraphQLError(message=update_dislikes['error'], extensions={"code": "BAD_USER_INPUT"})

            return update_dislikes.get("message")

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
    async def updateArtworkFavorites(self, info, updateArtworkFavoritesData: UpdateArtworkFavoritesInput) -> str:
        db = info.context["mongo_db"]
        current_user = info.context["current_user"]
        request = info.context["request"]
        
        awk_stts_service = ArtworkStatisticsService(db)

        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)
        try:
            userId = current_user.userId
            artworkId = updateArtworkFavoritesData.artworkId
            favorites = updateArtworkFavoritesData.favorites
            isFavorite = userId in updateArtworkFavoritesData.favorites

            update_favorites = await awk_stts_service.updateArtworkFavorites(artworkId=artworkId, favorites=favorites)
            if not update_favorites.get("ok", False):
                raise GraphQLError(message=update_favorites['error'], extensions={"code": "BAD_USER_INPUT"})

            migrateUserFavoriteArtworks.delay(userId, artworkId, isFavorite, ip, terminal)

            return update_favorites.get("message")

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
    async def updateCommentLikes(self, info, updateCommentLikesData: UpdateCommentLikesInput) -> str:
        db = info.context["mongo_db"]
        awk_stts_service = ArtworkStatisticsService(db)        
        try:
            update_likes = await awk_stts_service.updateCommentLikes(updateCommentLikesData.artworkId, updateCommentLikesData.commentId, updateCommentLikesData.likes)
            if not update_likes.get("ok", False):
                raise GraphQLError(message=update_likes['error'], extensions={"code": "BAD_USER_INPUT"})

            return update_likes.get("message")

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
    async def updateCommentDisLikes(self, info, updateCommentDisLikesData: UpdateCommentDisLikesInput) -> str:
        db = info.context["mongo_db"]
        awk_stts_service = ArtworkStatisticsService(db)        
        try:
            update_dislikes = await awk_stts_service.updateCommentDisLikes(updateCommentDisLikesData.artworkId, updateCommentDisLikesData.commentId, updateCommentDisLikesData.dislikes)
            if not update_dislikes.get("ok", False):
                raise GraphQLError(message=update_dislikes['error'], extensions={"code": "BAD_USER_INPUT"})

            return update_dislikes.get("message")

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