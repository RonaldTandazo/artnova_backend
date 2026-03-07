import strawberry
from app.config.logger import logger
from app.utils.helpers import Helpers
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.graphql.Block.BlockInputs import BlockStateInput
from app.services.Block.BlockService import BlockService

@strawberry.type
class BlockMutation:
    @strawberry.mutation
    async def setBlockState(self, info, data: BlockStateInput) -> str:
        db = info.context["db"]
        request = info.context["request"]
        current_user = info.context["current_user"]

        block_service = BlockService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)

        try:
            block_state = await block_service.verifyBlock(blockerId=current_user.userId, blockedId=data.blockedId)
            if not block_state.get("ok", False):
                raise GraphQLError(message=block_state['error'], extensions={"code": "BAD_USER_INPUT"})
            
            block_state = block_state.get('data')
            
            if not block_state['exists']:
                set_follow = await block_service.setBlock(blockerId=current_user.userId, blockedId=data.blockedId, ip=ip, terminal=terminal)
                if not set_follow.get("ok", False):
                    raise GraphQLError(message=set_follow['error'], extensions={"code": "BAD_USER_INPUT"})
                
            return "User Successfully Blocked"

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
    async def unsetBlockState(self, info, data: BlockStateInput) -> str:
        db = info.context["db"]
        current_user = info.context["current_user"]

        block_service = BlockService(db)
        
        try:
            block_state = await block_service.verifyBlock(blockerId=current_user.userId, blockedId=data.blockedId)
            if not block_state.get("ok", False):
                raise GraphQLError(message=block_state['error'], extensions={"code": "BAD_USER_INPUT"})
            
            block_state = block_state.get('data')
            
            if block_state['exists']:
                blockId = block_state['block_id']

                unset_block = await block_service.unsetBlock(blockId=blockId)
                if not unset_block.get("ok", False):
                    raise GraphQLError(message=unset_block['error'], extensions={"code": "BAD_USER_INPUT"})
                
            return "User Successfully Unblocked"

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