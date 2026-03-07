from app.celery.worker import celery_app
from app.db.database import get_mongo_celery
from app.models.Users.UserMongo import UserMongo
from app.utils.helpers import Helpers

@celery_app.task(name="migrate_users_mongo")
def migrateUserMongo(user_id, username, ip, terminal):
    async def _logic():
        db = get_mongo_celery()
        collection = db.get_collection("users")
        
        user = UserMongo(
            user_id=user_id,
            username=username,
            ip=ip,
            terminal=terminal
        )

        document_data = user.model_dump(by_alias=True, exclude_none=True)
        await collection.insert_one(document_data)

    Helpers.run_async(_logic())