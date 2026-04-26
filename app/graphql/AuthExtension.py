from fastapi import Request
from strawberry.extensions import SchemaExtension
from strawberry.exceptions import GraphQLError
from app.security.AuthGraph import getCurrentUserFromToken
from app.config.logger import logger

CONDITIONAL_AUTH_OPERATIONS = [
    "GetArtVerseArtworks",
    "GetArtworkDetails",
    "GetArtworkStatistics",
    "StoreArtworkViews",
    "GetSearchResults"
]

NO_AUTH_REQUIRED_OPERATIONS = [
    "RegisterUser",
    "Login",
    "RefreshToken",
    "RevokeToken"
]

class AuthExtension(SchemaExtension):
    def on_request_start(self) -> None:
        info = self.execution_context
        request: Request = info.context["request"]
        info.context["current_user"] = None 

        if request.scope['type'] == 'websocket':
            return
        
        body = info.context["body"]
        operation_name = body.get("operationName") if body else None

        if operation_name and operation_name in NO_AUTH_REQUIRED_OPERATIONS:
            return

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            if operation_name and operation_name in CONDITIONAL_AUTH_OPERATIONS:
                return
            else:
                raise GraphQLError(
                    message="Authentication is Required",
                    extensions={"code": "FORBIDDEN"}
                )
        
        try:
            token = authorization.split("Bearer ")[-1]
            current_user = getCurrentUserFromToken(token)

            if not current_user['ok']:
                raise GraphQLError(
                    message="Token has expired",
                    extensions={"code": "UNAUTHENTICATED"}
                )

            info.context["current_user"] = current_user['data']
        except GraphQLError as e:
            raise e
        except Exception:
            raise GraphQLError(
                message="Token is invalid",
                extensions={"code": "UNAUTHENTICATED"}
            )