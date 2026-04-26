import strawberry
from app.config.logger import logger
from app.graphql.Search.SearchInputs import SearchInput
from app.graphql.Search.SearchPayloads import SearchPayload
from app.services.Artwork.ArtworkService import ArtworkService
from app.services.User.UserService import UserService
from app.services.Block.BlockService import BlockService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError

@strawberry.type
class SearchQuery:
    @strawberry.field
    async def getSearchResults(self, info, input: SearchInput) -> SearchPayload:
        db = info.context["db"]
        current_user = info.context["current_user"]
        
        awk_service = ArtworkService(db)
        user_service = UserService(db)
        block_service = BlockService(db)

        try:
            artwork_response = []
            artwork_has_more = True
            artist_response = []
            artitst_has_more = True
            blockerIds = []

            userId = None
            if current_user:
                userId = current_user.userId

            if userId:
                blockers = await block_service.getBlockersByBlockedId(blockedId=userId)
                if not blockers.get("ok", False):
                    raise GraphQLError(message=blockers['error'], extensions={"code": "NOT_FOUND"})
                
                blockerIds = blockers.get("data")            

            if input.type == 'both' or input.type == 'artworks':
                artwork_results = await awk_service.getArtworksBySearch(search=input.search, page=input.pageArtworks, blockerIds=blockerIds)
                if not artwork_results.get("ok", False):
                    raise GraphQLError(message=artwork_results['error'], extensions={"code": "NOT_FOUND"})
                
                artwork_results = artwork_results.get('data')
                artwork_response = artwork_results['artworks']
                artwork_has_more = artwork_results['hasMore']

            if input.type == 'both' or input.type == 'artists':
                artists_results = await user_service.getArtistsBySearch(search=input.search, page=input.pageArtists, blockerIds=blockerIds)
                if not artists_results.get("ok", False):
                    raise GraphQLError(message=artists_results['error'], extensions={"code": "NOT_FOUND"})
                
                artists_results = artists_results.get('data')
                artist_response = artists_results['artists']
                artitst_has_more = artists_results['hasMore']

            return SearchPayload(
                artworks=artwork_response,
                hasMoreArtworks=artwork_has_more,
                artists=artist_response,
                hasMoreArtists=artitst_has_more,
                type=input.type
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
        