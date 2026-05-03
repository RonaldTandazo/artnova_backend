import os
import uuid
import json
import base64
import user_agents
from bson.objectid import ObjectId
from datetime import datetime, timezone
from app.config.logger import logger
import asyncio
import shutil

class Helpers:
    async def getIp(request) -> str:
        client_host = request.client.host
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        x_real_ip = request.headers.get("X-Real-IP")

        if x_forwarded_for:
            client_host = x_forwarded_for.split(",")[0]
        elif x_real_ip:
            client_host = x_real_ip

        return client_host

    async def getRequestAgents(request):
        user_agents_string = request.headers.get("user-agent")
        ua = user_agents.parse(user_agents_string)

        return {
            "device": ua.device.family,
            "os": ua.os.family,
            "browser": ua.browser.family,
        }
    
    async def getDateTime():
        now_utc = datetime.now(timezone.utc)
        formatted_now_utc = now_utc.strftime("%Y-%m-%d %H:%M:%S")

        return formatted_now_utc
    
    async def prepareAccessTokenData(user):
        structure = {
            "sub": user.username,
            "userId": user.user_id,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email,
            "username": user.username,
            "professionalHeadline": user.professional_headline,
            "summary": user.summary,
            "city": user.city,
            "countryId": user.country_id,
            "location": f"{user.city}, {user.country.name}" if user.country else None,
            "since": user.created_at.isoformat() if user.created_at else None,
            "avatar": user.avatar,
            "cover": user.cover
        }
        
        return structure
    
    async def generateRandomFilename(extension):
        filename = f"{uuid.uuid4()}{extension}"
        return filename
    
    async def decodedAndSaveFile(filename: str, file: str, type: str, decode: bool = True, artworkId: str = None):
        try:
            if decode:
                file_data  = base64.b64decode(file.split(',')[1])
            else:
                file_data = file

            upload_folder = "app/public"

            if type == "avatar":
                upload_folder += "/users/avatars"

            if type == "cover":
                upload_folder += "/users/covers"

            if type == "thumbnail":
                upload_folder += "/artworks/thumbnails"

            if type == "image":
                upload_folder += "/artworks/multimedia/images"

            if type == "video":
                upload_folder += "/artworks/multimedia/videos"

            if type == "model":
                upload_folder += "/artworks/model/"+artworkId

            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, filename)

            with open(file_path, "wb") as f:
                f.write(file_data)

            return {"ok": True, "message": "File Saved Successfully", "code": 201, "data": None}
        except Exception as e:
            logger.error(e)
            return {"ok": False, "error": "Error Saving File", "code": 500}
        
    async def deleteFile(filename: str, type: str, artworkId: str = None):
        try:
            base_folder = "app/public"
            target_folder = base_folder
            
            if type == "avatar":
                target_folder += "/users/avatars"

            elif type == "cover":
                target_folder += "/users/covers"

            elif type == "thumbnail":
                target_folder += "/artworks/thumbnails"
            
            elif type == "image":
                target_folder += "/artworks/multimedia/images"

            elif type == "video":
                target_folder += "/artworks/multimedia/videos"

            elif type == "model":
                folder_path_to_delete = os.path.join(base_folder, "artworks/models", str(artworkId))
            
                if os.path.exists(folder_path_to_delete):
                    shutil.rmtree(folder_path_to_delete)
                    
                    return {"ok": True, "message": "Model Folder Deleted Successfully", "code": 200}
                else:
                    return {"ok": False, "error": "Folder not found", "code": 404}

            file_path_to_delete = os.path.join(target_folder, filename)

            if os.path.exists(file_path_to_delete):
                os.remove(file_path_to_delete)

            return {"ok": True, "message": "File Deleted Successfully", "code": 200}
        except Exception as e:
            logger.error(e)
            return {"ok": False, "error": "Error Deleting File", "code": 500}

    @staticmethod  
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        raise TypeError (f"Object of type {type(obj).__name__} is not JSON serializable")

    @staticmethod
    def dumps_with_mongo_types(data: dict) -> str:
        return json.dumps(data, default=Helpers.json_serial)
    
    @staticmethod
    def run_async(coro):
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)