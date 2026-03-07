import strawberry
from app.config.logger import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.services.General.CategoryService import CategoryService
from app.services.General.TopicService import TopicService
from app.services.General.SoftwareService import SoftwareService
from app.services.General.CategoryService import CategoryService
from app.services.User.UserTopicService import UserTopicService
from app.services.User.UserSoftwareService import UserSoftwareService
from app.services.User.UserCategoryService import UserCategoryService
from app.services.User.UserService import UserService
from app.graphql.User.UserPayloads import SkillsData
from app.graphql.Category.CategoryPayloads import CategoryPayload
from app.graphql.Topic.TopicPayloads import TopicPayload
from app.graphql.Software.SoftwarePayloads import SoftwarePayload
from app.graphql.UserSkills.UserSkillsInputs import UserSkillsInput
from app.graphql.UserSkills.UserSkillsPayloads import UserSkillsPayload
from app.utils.helpers import Helpers

@strawberry.type
class UserSkillsQuery:
    @strawberry.field
    async def getUserSkills(self, info) -> UserSkillsPayload:
        db = info.context["db"]
        current_user = info.context["current_user"]
        usr_tpc_service = UserTopicService(db)
        usr_sft_service = UserSoftwareService(db)
        usr_ctg_service = UserCategoryService(db)
        try:
            user_topics = await usr_tpc_service.getUserTopics(current_user.userId)
            if not user_topics.get("ok", False):
                raise GraphQLError(message=user_topics['error'], extensions={"code": "BAD_USER_INPUT"})
            
            user_topics = user_topics.get("data")

            user_softwares = await usr_sft_service.getUserSoftwares(current_user.userId)
            if not user_softwares.get("ok", False):
                raise GraphQLError(message=user_softwares['error'], extensions={"code": "BAD_USER_INPUT"})
            
            user_softwares = user_softwares.get("data")

            user_categories = await usr_ctg_service.getUserCategories(current_user.userId)
            if not user_categories.get("ok", False):
                raise GraphQLError(message=user_categories['error'], extensions={"code": "BAD_USER_INPUT"})
            
            user_categories = user_categories.get("data")

            return UserSkillsPayload(userCategories=user_categories, userSoftwares=user_softwares, userTopics=user_topics)
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
    async def getSkillsData(self, info) ->SkillsData:
        db = info.context["db"]
        ctg_service = CategoryService(db)
        tpc_service = TopicService(db)
        sft_service = SoftwareService(db)
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

            return SkillsData(categories=categories, topics=topics, softwares=softwares)
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
class UserSkillsMutation:
    @strawberry.mutation
    async def storeUserSkills(self, info, userSkillsData: UserSkillsInput) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]
        request = info.context["request"]

        usr_ctg_service = UserCategoryService(db)
        usr_sftw_service = UserSoftwareService(db)
        usr_tpc_service = UserTopicService(db)
        usr_service = UserService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)
        try:
            user = await usr_service.getUserById(current_user.userId)
            if not user.get("ok", False):
                raise GraphQLError(message=user['error'], extensions={"code": "BAD_USER_INPUT"})
            
            if userSkillsData.categories and len(userSkillsData.categories) > 0:
                delete_categories = await usr_ctg_service.deleteUserCategories(current_user.userId, userSkillsData.categories)
                if not delete_categories.get("ok", False):
                    raise GraphQLError(message=delete_categories['error'], extensions={"code": "BAD_USER_INPUT"})
                
                categoryIds = []

                for categoryId in userSkillsData.categories:
                    existing_category = await usr_ctg_service.validateUserCategory(current_user.userId, categoryId)
                    if not existing_category.get("ok", False):
                        raise GraphQLError(message=existing_category['error'], extensions={"code": "BAD_USER_INPUT"})
                    
                    if not existing_category.get('data'):
                        categoryIds.append(categoryId)

                store_categories = await usr_ctg_service.storeUserCategories(current_user.userId, categoryIds, terminal, ip)
                if not store_categories.get("ok", False):
                    raise GraphQLError(message=store_categories['error'], extensions={"code": "BAD_USER_INPUT"})
            elif len(userSkillsData.categories) == 0:
                delete_all_categories = await usr_ctg_service.deleteAllUserCategories(current_user.userId)
                if not delete_all_categories.get("ok", False):
                    raise GraphQLError(message=delete_all_categories['error'], extensions={"code": "BAD_USER_INPUT"})
                
            if userSkillsData.topics and len(userSkillsData.topics) > 0:
                delete_topics = await usr_tpc_service.deleteUserTopics(current_user.userId, userSkillsData.topics)
                if not delete_topics.get("ok", False):
                    raise GraphQLError(message=delete_topics['error'], extensions={"code": "BAD_USER_INPUT"})
                
                topicIds = []

                for topicId in userSkillsData.topics:
                    existing_topic = await usr_tpc_service.validateUserTopic(current_user.userId, topicId)
                    if not existing_topic.get("ok", False):
                        raise GraphQLError(message=existing_topic['error'], extensions={"code": "BAD_USER_INPUT"})
                    
                    if not existing_topic.get('data'):
                        topicIds.append(topicId)

                store_topics = await usr_tpc_service.storeUserTopics(current_user.userId, topicIds, terminal, ip)
                if not store_topics.get("ok", False):
                    raise GraphQLError(message=store_topics['error'], extensions={"code": "BAD_USER_INPUT"})
            elif len(userSkillsData.topics) == 0:
                delete_all_topics = await usr_tpc_service.deleteAllUserTopics(current_user.userId)
                if not delete_all_topics.get("ok", False):
                    raise GraphQLError(message=delete_all_topics['error'], extensions={"code": "BAD_USER_INPUT"})
                
            if userSkillsData.softwares and len(userSkillsData.softwares) > 0:
                delete_softwares = await usr_sftw_service.deleteUserSoftwares(current_user.userId, userSkillsData.softwares)
                if not delete_softwares.get("ok", False):
                    raise GraphQLError(message=delete_softwares['error'], extensions={"code": "BAD_USER_INPUT"})
                
                softwareIds = []

                for softwareId in userSkillsData.softwares:
                    existing_software = await usr_sftw_service.validateUserSoftware(current_user.userId, softwareId)
                    if not existing_software.get("ok", False):
                        raise GraphQLError(message=existing_software['error'], extensions={"code": "BAD_USER_INPUT"})
                    
                    if not existing_software.get('data'):
                        softwareIds.append(softwareId)

                store_softwares = await usr_sftw_service.storeUserSoftwares(current_user.userId, softwareIds, terminal, ip)
                if not store_softwares.get("ok", False):
                    raise GraphQLError(message=store_softwares['error'], extensions={"code": "BAD_USER_INPUT"})
            elif len(userSkillsData.softwares) == 0:
                delete_all_softwares = await usr_sftw_service.deleteAllUserSoftwares(current_user.userId)
                if not delete_all_softwares.get("ok", False):
                    raise GraphQLError(message=delete_all_softwares['error'], extensions={"code": "BAD_USER_INPUT"})
                
            await db.commit()

            return "Skills && Interests Updated Successfully"
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