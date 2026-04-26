import os
import redis.asyncio as redis
from redis.asyncio.client import Redis
from app.config.logger import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://default:AZwxgEDMZBLPnix1PZP5PlEYrCIcAYw5@redis-17903.c90.us-east-1-3.ec2.cloud.redislabs.com:17903")

redis_client: Redis = None

async def connect_to_redis():
    global redis_client
    
    redis_client = redis.from_url(
        REDIS_URL, 
        decode_responses=True
    )
    
    await redis_client.ping() 

async def close_redis_connection():
    if redis_client:
        await redis_client.close()

def get_redis_client() -> Redis:
    global redis_client

    if redis_client is None:
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True
        )
    
    return redis_client