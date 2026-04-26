import strawberry
from app.config.logger import logger
from app.utils.helpers import Helpers
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.graphql.Follow.FollowInputs import FollowStateInput
from app.graphql.Follow.FollowPayloads import FollowStatePayload
from app.services.Follow.FollowService import FollowService
from app.jobs.Notification.SendFollowerNotification import sendFollowerNotification

@strawberry.type
class FollowQuery:
    @strawberry.field
    async def getFollowState(self, info, data: FollowStateInput) -> FollowStatePayload:
        db = info.context["db"]
        current_user = info.context["current_user"]

        follow_service = FollowService(db)

        try:
            follow_state = await follow_service.verifyRelationship(followerId=current_user.userId, followedId=data.followedId)
            if not follow_state.get("ok", False):
                raise GraphQLError(message=follow_state['error'], extensions={"code": "BAD_USER_INPUT"})
            
            follow_state = follow_state.get('data')
            exists = follow_state['exists']
                
            return FollowStatePayload(isFollowed=exists)

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
class FollowMutation:
    @strawberry.mutation
    async def setFollowState(self, info, data: FollowStateInput) -> str:
        db = info.context["db"]
        request = info.context["request"]
        current_user = info.context["current_user"]

        follow_service = FollowService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)

        try:
            follow_state = await follow_service.verifyRelationship(followerId=current_user.userId, followedId=data.followedId)
            if not follow_state.get("ok", False):
                raise GraphQLError(message=follow_state['error'], extensions={"code": "BAD_USER_INPUT"})
            
            follow_state = follow_state.get('data')
            
            if not follow_state['exists']:
                set_follow = await follow_service.setFollow(followerId=current_user.userId, followedId=data.followedId, ip=ip, terminal=terminal)
                if not set_follow.get("ok", False):
                    raise GraphQLError(message=set_follow['error'], extensions={"code": "BAD_USER_INPUT"})
                
                sendFollowerNotification.delay(current_user.userId, data.followedId, ip, terminal)
                
            await db.commit()
                
            return "Relationship Set"

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
    async def unsetFollowState(self, info, data: FollowStateInput) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]

        follow_service = FollowService(db)
        
        try:
            if data.simple:
                follow_state = await follow_service.verifyRelationship(followerId=current_user.userId, followedId=data.followedId)
                if not follow_state.get("ok", False):
                    raise GraphQLError(message=follow_state['error'])
                
                state_data = follow_state.get('data')
                if state_data['exists']:
                    unset_follow = await follow_service.unsetFollow(followId=state_data['follow_id'])
                    if not unset_follow.get("ok", False):
                        raise GraphQLError(message=unset_follow['error'], extensions={"code": "BAD_USER_INPUT"})
            else:
                unset_follows = await follow_service.unsetMutualFollow(userA=current_user.userId, userB=data.followedId)
                if not unset_follows.get("ok", False):
                    raise GraphQLError(message=unset_follows['error'])

            await db.commit()
            
            return "Relationship Unset"

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