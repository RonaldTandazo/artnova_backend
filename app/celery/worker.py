import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://default:AZwxgEDMZBLPnix1PZP5PlEYrCIcAYw5@redis-17903.c90.us-east-1-3.ec2.cloud.redislabs.com:17903")

celery_app = Celery(
    'worker',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'app.jobs.User.MigrateUserMongo',
        'app.jobs.User.UpdateUserAvatarMongo',
        'app.jobs.Artwork.CreateArtworkStats',
        'app.jobs.Artwork.MigrateUserFavoriteArtworks',
        'app.jobs.Artwork.DeleteArtworksRecords'
    ]
)

celery_app.conf.update(
    result_expires=3600,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True
)

celery_app.conf.beat_schedule = {
    # 'limpiar-cache-todos-los-dias': {
    #     'task': 'app.jobs.system.tasks.limpiar_cache',
    #     'schedule': crontab(hour=7, minute=30),
    # },
}