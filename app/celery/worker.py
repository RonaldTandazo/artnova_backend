import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://default:qhBTTkTBTdLBJPn20rJw795Xzu8tSwDt@redis-12617.c13.us-east-1-3.ec2.cloud.redislabs.com:12617"
)

celery_app = Celery(
    'worker',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'app.jobs.User.MigrateUserMongo',
        'app.jobs.User.UpdateUserAvatar',
        'app.jobs.Artwork.CreateArtworkStats',
        'app.jobs.Artwork.CreateArtworkModel',
        'app.jobs.Artwork.MigrateUserFavoriteArtworks',
        'app.jobs.Artwork.DeleteArtworksRecords',
        "app.jobs.Artwork.PublishScheduledArtworks",
        "app.jobs.Notification.SendArtworkNotification",
        "app.jobs.Notification.SendFollowerNotification"
    ]
)

celery_app.conf.update(
    result_expires=3600,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300
)

celery_app.conf.beat_schedule = {
    'publish-scheduled-artworks-every-hour': {
        'task': 'publish_scheduled_artworks',
        'schedule': crontab(minute=0),
    },
}