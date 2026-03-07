import json
from app.utils.helpers import Helpers
from app.config.logger import logger
from app.db.redis import get_redis_client

class PubSubManager:
    async def publish(self, channel: str, message_data: dict):
        redis_client = get_redis_client()

        try:
            serialized_data = Helpers.dumps_with_mongo_types(message_data)
            await redis_client.publish(channel, serialized_data)
        
        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}")

    async def subscribe(self, channel: str):
        redis_client = get_redis_client()

        pubsub = redis_client.pubsub()

        await pubsub.subscribe(channel)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                yield json.loads(message['data'])