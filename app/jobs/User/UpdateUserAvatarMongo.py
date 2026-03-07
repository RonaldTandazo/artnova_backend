from app.celery.worker import celery_app
from app.db.database import get_mongo_celery
from app.utils.helpers import Helpers
from app.config.logger import logger

@celery_app.task(name="update_avatar_mongo")
def updateAvatarMongo(user_id, filename):
    async def _logic():
        db = get_mongo_celery()
        collection = db.get_collection("artwork_statistics")

        await collection.update_many(
            {"comments.user_id": user_id},
            {
                "$set": {
                    "comments.$[comment].avatar": filename
                }
            },
            array_filters=[{"comment.user_id": user_id}]
        )

    Helpers.run_async(_logic())