from app.celery.worker import celery_app
from app.db.database import get_mongo_celery
from app.services.ArtworkModel.ArtworkModelService import ArtworkModelService
from app.utils.helpers import Helpers

@celery_app.task(name="create_artwork_model")
def createArtworkModel(artworkId, ownerId, mainFile, resources, settings, ip, terminal):
    async def _logic():
        db = get_mongo_celery()
        
        model_service = ArtworkModelService(db)
        await model_service.store(artworkId=artworkId, ownerId=ownerId, mainFile=mainFile, resources=resources, settings=settings, ip=ip, terminal=terminal)

    return Helpers.run_async(_logic())