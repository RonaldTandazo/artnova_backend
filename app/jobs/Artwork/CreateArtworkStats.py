from app.celery.worker import celery_app
from app.db.database import get_mongo_celery
from app.services.ArtworkStatistics.ArtworkStatisticsService import ArtworkStatisticsService
from app.utils.helpers import Helpers

@celery_app.task(name="create_artwork_stats")
def createArtworkStats(artworkId, ownerId, ip, terminal):
    async def _logic():
        db = get_mongo_celery()
        
        stats_service = ArtworkStatisticsService(db)
        await stats_service.store(artworkId=artworkId, ownerId=ownerId, ip=ip, terminal=terminal)

    return Helpers.run_async(_logic())