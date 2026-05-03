import strawberry
import asyncio
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.utils.helpers import Helpers
from app.graphql.Artwork.ArtworkInputs import StoreArtworkInput, DeleteUserArtworkInput
from app.graphql.Authentication.AuthInputs import ValidateAccessInput
from app.graphql.Artwork.ArtworkPayloads import ArtworkPayload, ArtworkDetailsPayload, ArtworkFormData, ArtworkItemPayload, ArtworkModelPayload
from app.graphql.ArtworkStatistics.ArtworkStatisticsPayloads import ArtworkStatsPayload
from app.services.Artwork.ArtworkService import ArtworkService
from app.services.Artwork.ArtworkOwnerService import ArtworkOwnerService
from app.services.Artwork.ArtworkThumbnailService import ArtworkThumbnailService
from app.services.Artwork.ArtworkCategoryService import ArtworkCategoryService
from app.services.Artwork.ArtworkSoftwareService import ArtworkSoftwareService
from app.services.Artwork.ArtworkTopicService import ArtworkTopicService
from app.services.Artwork.ArtworkImageService import ArtworkImageService
from app.services.Artwork.ArtworkVideoService import ArtworkVideoService
from app.services.Artwork.ArtworkScheduleService import ArtworkScheduleService
from app.services.ArtworkStatistics.ArtworkStatisticsService import ArtworkStatisticsService
from app.services.Artwork.ArtworkUserFavoriteService import ArtworkUserFavoriteService
from app.services.ArtworkModel.ArtworkModelService import ArtworkModelService
from app.services.General.CategoryService import CategoryService
from app.services.General.TopicService import TopicService
from app.services.General.SoftwareService import SoftwareService
from app.services.General.PublishingService import PublishingService
from app.graphql.Category.CategoryPayloads import CategoryPayload
from app.graphql.Topic.TopicPayloads import TopicPayload
from app.graphql.Software.SoftwarePayloads import SoftwarePayload
from app.graphql.Publishing.PublishingPayloads import PublishingPayload
from typing import AsyncGenerator
from app.jobs.Artwork.CreateArtworkStats import createArtworkStats
from app.jobs.Artwork.CreateArtworkModel import createArtworkModel
from app.jobs.Artwork.DeleteArtworksRecords import deleteArtworksRecords
from app.jobs.Notification.SendArtworkNotification import sendArtworkNotification

@strawberry.type
class NewArtworkPayload:
    artwork: ArtworkPayload

artwork_queue: asyncio.Queue[NewArtworkPayload] = asyncio.Queue()

async def artwork_creation_generator():
    while True:
        new_artwork_payload = await artwork_queue.get()
        yield new_artwork_payload

@strawberry.type
class ArtworkMutation:
    @strawberry.mutation
    async def storeArtwork(self, info, artworkData: StoreArtworkInput) -> ArtworkPayload:
        db = info.context["db"]
        current_user = info.context["current_user"]
        request = info.context["request"]

        awk_service = ArtworkService(db)
        awk_owner_service = ArtworkOwnerService(db)
        awk_thmb_service = ArtworkThumbnailService(db)
        awk_ctg_service = ArtworkCategoryService(db)
        awk_sfw_service = ArtworkSoftwareService(db)
        awk_tpc_service = ArtworkTopicService(db)
        awk_img_service = ArtworkImageService(db)
        awk_vid_service = ArtworkVideoService(db)
        awk_sch_service = ArtworkScheduleService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)
        thumbnameFilename = None

        try:
            has_thumbnail = bool(artworkData.thumbnail)
            has_images = bool(artworkData.images)
            has_videos = bool(artworkData.videos)
            has_3d_file = bool(artworkData.modelMainFile)
            has_categories = artworkData.categories and len(artworkData.categories) > 0
            has_topics = artworkData.topics and len(artworkData.topics) > 0
            has_softwares = artworkData.softwares and len(artworkData.softwares) > 0

            store_artwork = await awk_service.store(
                title=artworkData.title,
                description=artworkData.description,
                matureContent=artworkData.matureContent,
                has_images=has_images,
                has_videos=has_videos,
                has_3d_file=has_3d_file,
                ip=ip,
                terminal=terminal,
                publishing=artworkData.publishing
            )
            if not store_artwork.get("ok", False):
                raise GraphQLError(message=store_artwork['error'], extensions={"code": "BAD_USER_INPUT"})

            artwork = store_artwork.get("data")

            store_artwork_owner = await awk_owner_service.store(
                artworkId=artwork.artwork_id,
                userId=current_user.userId,
                ip=ip,
                terminal=terminal
            )
            if not store_artwork_owner.get("ok", False):
                raise GraphQLError(message=store_artwork_owner['error'], extensions={"code": "BAD_USER_INPUT"})

            if has_categories:
                store_artwork_categories = await awk_ctg_service.store(
                    artworkId=artwork.artwork_id,
                    categoryIds=artworkData.categories,
                    ip=ip,
                    terminal=terminal
                )
                if not store_artwork_categories.get("ok", False):
                    raise GraphQLError(message=store_artwork_categories['error'], extensions={"code": "BAD_USER_INPUT"})
                
            if has_topics:
                store_artwork_topics = await awk_tpc_service.store(
                    artworkId=artwork.artwork_id,
                    topicIds=artworkData.topics,
                    ip=ip,
                    terminal=terminal
                )
                if not store_artwork_topics.get("ok", False):
                    raise GraphQLError(message=store_artwork_topics['error'], extensions={"code": "BAD_USER_INPUT"})
                
            if has_softwares:
                store_artwork_softwares = await awk_sfw_service.store(
                    artworkId=artwork.artwork_id,
                    softwareIds=artworkData.softwares,
                    ip=ip,
                    terminal=terminal
                )
                if not store_artwork_softwares.get("ok", False):
                    raise GraphQLError(message=store_artwork_softwares['error'], extensions={"code": "BAD_USER_INPUT"})
                
            if has_images:
                for index, image in enumerate(artworkData.images):
                    image_name = artworkData.title+ " _ Image " + str(index)
                    filename = await Helpers.generateRandomFilename(".jpeg")
                    image_content = await image.read()

                    image_store = await Helpers.decodedAndSaveFile(filename, image_content, "image", False)
                    if not image_store.get("ok", False):
                        raise GraphQLError(message=image_store['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})

                    store_artwork_image = await awk_img_service.store(
                        artworkId=artwork.artwork_id, 
                        filename=filename, 
                        image_name=image_name,
                        ip=ip,
                        terminal=terminal
                    )

                    if not store_artwork_image.get("ok", False):
                        raise GraphQLError(message=store_artwork_image['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
                    
            if has_videos:
                for index, video in enumerate(artworkData.videos):
                    video_name = artworkData.title+ " _ Video " + str(index)
                    filename = await Helpers.generateRandomFilename(".mp4")
                    video_content = await video.read()

                    video_store = await Helpers.decodedAndSaveFile(filename, video_content, "video", False)
                    if not video_store.get("ok", False):
                        raise GraphQLError(message=video_store['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})

                    store_artwork_video = await awk_vid_service.store(
                        artworkId=artwork.artwork_id, 
                        filename=filename, 
                        video_name=video_name,
                        ip=ip,
                        terminal=terminal
                    )

                    if not store_artwork_video.get("ok", False):
                        raise GraphQLError(message=store_artwork_video['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
                
            if has_thumbnail:
                thumbnail_name = artworkData.title+" Thumbnail"
                filename = await Helpers.generateRandomFilename(".jpeg")
                thumbnail_content = await artworkData.thumbnail.read()
                thumbnameFilename = filename

                thumbnail_store = await Helpers.decodedAndSaveFile(filename, thumbnail_content, "thumbnail", False)
                if not thumbnail_store.get("ok", False):
                    raise GraphQLError(message=thumbnail_store['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})

                store_artwork_thumbnail = await awk_thmb_service.store(
                    artworkId=artwork.artwork_id, 
                    filename=filename, 
                    thumbnail_name=thumbnail_name,
                    ip=ip,
                    terminal=terminal
                )

                if not store_artwork_thumbnail.get("ok", False):
                    raise GraphQLError(message=store_artwork_thumbnail['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})

            if artworkData.publishing == 4 and artworkData.publishingTargetStatus != None:
                store_schedule = await awk_sch_service.store(
                    artworkId=artwork.artwork_id,
                    publishingIdTarget=artworkData.publishingTargetStatus,
                    scheduleAt=artworkData.scheduleAt,
                    ip=ip,
                    terminal=terminal
                )
                if not store_schedule.get("ok", False):
                    raise GraphQLError(message=store_schedule['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})

            await db.commit()
            await artwork_queue.put(
                NewArtworkPayload(
                    artwork=ArtworkPayload(
                        artworkId=artwork.artwork_id,
                        title=artwork.title,
                        thumbnail=thumbnameFilename,
                        publishingId=artworkData.publishing,
                        owner=current_user.userId,
                        createdAt=artwork.created_at
                    )
                )
            )

            createArtworkStats.delay(artwork.artwork_id, current_user.userId, ip, terminal)

            if has_3d_file:
                mainFile_name = artworkData.modelMainFile.filename
                model_content = await artworkData.modelMainFile.read()

                modelSettings = strawberry.asdict(artworkData.modelSettings)

                model_store = await Helpers.decodedAndSaveFile(filename=mainFile_name, file=model_content, type="model", decode=False, artworkId=str(artwork.artwork_id))
                if not model_store.get("ok", False):
                    raise GraphQLError(message=model_store['error'], extensions={"code": "INTERNAL_SERVER_ERROR"})
                
                resourceFilenames = []
                if artworkData.modelResources:
                    for resource in artworkData.modelResources:
                        res_name = resource.filename
                        res_content = await resource.read()
                        
                        res_store = await Helpers.decodedAndSaveFile(filename=res_name, file=res_content, type="model", decode=False, artworkId=str(artwork.artwork_id))
                        
                        if res_store.get("ok"):
                            resourceFilenames.append(res_name)

                createArtworkModel.delay(artwork.artwork_id, current_user.userId, mainFile_name, resourceFilenames, modelSettings, ip, terminal)

            if artworkData.publishing == 2:
                sendArtworkNotification.delay(current_user.userId, current_user.username, artwork.artwork_id, thumbnameFilename, ip, terminal)

            return ArtworkPayload(
                artworkId=artwork.artwork_id,
                title=artwork.title,
                thumbnail=thumbnameFilename,
                publishingId=artworkData.publishing,
                owner=current_user.userId,
                createdAt=artwork.created_at
            )

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
    async def deleteUserArtworks(self, info, deleteArtworks: DeleteUserArtworkInput) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        awk_owner_service = ArtworkOwnerService(db)

        try:
            userId=current_user.userId

            validation = await awk_owner_service.validateArtworksOwner(userId=userId, ArtworkIds=deleteArtworks.artworkIds)
            if validation.get('ok'):
                result = validation.get('data')
                owned_ids = result['owned_ids']

                deleteArtworksRecords.delay(owned_ids)

            return 'ArtWork/s Deleted Successfully'

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
        
@strawberry.type
class ArtworkQuery:
    @strawberry.field
    async def getArtVerseArtworks(self, info) -> list[ArtworkPayload]:
        db = info.context["db"]
        awk_service = ArtworkService(db)

        try:
            artworks = await awk_service.getArtVerseArtworks()
            if not artworks.get("ok", False):
                raise GraphQLError(message=artworks['error'], extensions={"code": "NOT_FOUND"})
            
            artworks = artworks.get("data")

            return artworks
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
        
    @strawberry.field
    async def getUserArtworks(self, info, data: ValidateAccessInput) -> list[ArtworkItemPayload]:
        db = info.context["db"]
        mongo = info.context["mongo_db"]

        current_user = info.context["current_user"]
        awk_owner_service = ArtworkOwnerService(db)
        awk_stats_service = ArtworkStatisticsService(mongo)

        try:
            if data.module == 'VisitProfile':
                userId = data.value
            else:
                userId = current_user.userId

            artworks = await awk_owner_service.getUserArtworks(userId=userId)
            if not artworks.get("ok", False):
                raise GraphQLError(message=artworks['error'], extensions={"code": "NOT_FOUND"})
            
            artworks_stats = await awk_stats_service.getUserArtworks(userId=userId)
            if not artworks_stats.get("ok", False):
                raise GraphQLError(message=artworks_stats['error'], extensions={"code": "NOT_FOUND"})
            
            artworks = artworks.get("data")
            artworks_stats = artworks_stats.get("data")

            stats_map = {stat["artwork_id"]: stat["stats"] for stat in artworks_stats}

            payload = []

            for artwork in artworks:
                stats = stats_map.get(artwork['artworkId'], {})

                payload.append(
                    ArtworkItemPayload(
                        artworkId=artwork['artworkId'],
                        title=artwork['title'],
                        thumbnail=artwork['thumbnail'],
                        publishingId=artwork['publishingId'],
                        scheduleAt=artwork['scheduleAt'],
                        stats=ArtworkStatsPayload(
                            viewsAmount=stats.get("views_amount", 0),
                            likes=stats.get("likes", []),
                            dislikes=stats.get("dislikes", []),
                            favorites=stats.get("favorites", []),
                            commentsAmount=stats.get("comments_amount", 0),
                        )
                    )
                )

            return payload
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
        
    @strawberry.field
    async def getUserFavoritesArtworks(self, info) -> list[ArtworkPayload]:
        db = info.context["db"]

        current_user = info.context["current_user"]
        awk_fav_service = ArtworkUserFavoriteService(db)

        try:
            fav_artworks = await awk_fav_service.getFavoritesArtworksByUser(userId=current_user.userId)
            if not fav_artworks.get("ok", False):
                raise GraphQLError(message=fav_artworks['error'], extensions={"code": "NOT_FOUND"})
            
            artworks = fav_artworks.get("data")

            return artworks
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
        
    @strawberry.field
    async def getArtworkDetails(self, info, artworkId: int) -> ArtworkDetailsPayload:
        db = info.context["db"]
        awk_service = ArtworkService(db)

        try:
            artwork = await awk_service.getArtworkDetails(artworkId=artworkId)
            if not artwork.get("ok", False):
                raise GraphQLError(message=artwork['error'], extensions={"code": "NOT_FOUND"})
            
            artwork = artwork.get("data")

            return ArtworkDetailsPayload(
                artworkId=artwork['artwork_id'], 
                title=artwork['title'], 
                description=artwork['description'], 
                matureContent=artwork['mature_content'], 
                categories=artwork['categories'], 
                topics=artwork['topics'], 
                softwares=artwork['softwares'],
                publishingId=artwork['publishing_id'], 
                thumbnail=artwork['thumbnail'], 
                hasImages=artwork['hasImages'],
                images=artwork['images'],
                hasVideos=artwork['hasVideos'],
                videos=artwork['videos'],
                has3DFile=artwork['has3DFile'],
                owner=artwork['owner'],
                createdAt=artwork['created_at']
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
        
    @strawberry.field
    async def getArtworkFormData(self, info) ->ArtworkFormData:
        db = info.context["db"]
        ctg_service = CategoryService(db)
        tpc_service = TopicService(db)
        sft_service = SoftwareService(db)
        pbl_service = PublishingService(db)

        try:
            categories = await ctg_service.getCategories()
            categories = categories.get("data") if categories.get("ok") else []
            categories = [
                CategoryPayload(categoryId=item.category_id, name=item.name)
                for item in categories
            ]

            topics = await tpc_service.getTopics()
            topics = topics.get("data") if topics.get("ok") else []
            topics = [
                TopicPayload(topicId=item.topic_id, name=item.name)
                for item in topics
            ]

            softwares = await sft_service.getSoftware()
            softwares = softwares.get("data") if softwares.get("ok") else []
            softwares = [
                SoftwarePayload(softwareId=item.software_id, name=item.name)
                for item in softwares
            ]

            publishing = await pbl_service.getPublishing()
            publishing = publishing.get("data") if publishing.get("ok") else []
            publishing = [
                PublishingPayload(publishingId=item.publishing_id, name=item.name, type=item.type)
                for item in publishing
            ]

            return ArtworkFormData(categories=categories, topics=topics, softwares=softwares, publishing=publishing)
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
        
    @strawberry.field
    async def getArtworkModel(self, info, artworkId: int) -> ArtworkModelPayload:
        mongo = info.context["mongo_db"]
        awk_model_service = ArtworkModelService(mongo)

        try:
            model = await awk_model_service.getArtworkModel(artworkId=artworkId)
            if not model.get("ok", False):
                raise GraphQLError(message=model['error'], extensions={"code": "NOT_FOUND"})
            
            model = model.get("data")

            return ArtworkModelPayload(
                mainFile=model['mainFile'], 
                resources=model['resources'], 
                settings=model['settings'], 
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
class ArtworkSubscription:
    @strawberry.subscription
    async def newArtwork(self) -> AsyncGenerator[NewArtworkPayload, None]:
        async for artwork_payload in artwork_creation_generator():
            yield artwork_payload