from fastapi import HTTPException, Depends, status
from app.schemas.TokenData import TokenData
from jose import jwt, JWTError, ExpiredSignatureError
from app.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from app.config.logger import logger
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from strawberry.exceptions import GraphQLError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def createAccessToken(data: dict, expires_delta: timedelta = None):
    try:
        if expires_delta is None:
            expires_delta = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        logger.error(f"Error creating JWT: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating JWT token.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error while creating JWT.")
    
def createRefreshToken(data: dict, expires_delta: timedelta = None):
    try:
        if expires_delta is None:
            expires_delta = timedelta(minutes=int(REFRESH_TOKEN_EXPIRE_MINUTES))
        
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return {"token":encoded_jwt, "expire_at":expire}
    except JWTError as e:
        logger.error(f"Error creating JWT Refresh Token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating JWT Refresh Token.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error while creating JWT Refresh Token.")

def verifyToken(token: str, origin: str | None = None):
    options = {"verify_exp": True}

    if origin == 'Revoke':
        options["verify_exp"] = False

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options=options)
        return payload
    except ExpiredSignatureError as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "Expired"
    except JWTError as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "Invalid"

def getCurrentUserFromToken(token: str = Depends(oauth2_scheme)):
    try:
        payload = verifyToken(token)
        if payload == "Expired":
            return {"ok": False,"error": "Token has expired","code": 401}
        elif payload == "Invalid":
            return {"ok": False,"error": "Token is invalid","code": 401}
    
        username = payload.get("sub")
        userId = payload.get("userId")
        if not username:
            raise GraphQLError(
                message="Could not validate credentials", 
                extensions={"code": "UNAUTHENTICATED"}
            )
        
        return {"ok": True, "data": TokenData(username=username, userId=userId)}
    except:
        return {"ok": False, "error": "Token is invalid","code": 401}