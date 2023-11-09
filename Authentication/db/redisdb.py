import redis.asyncio as redis

from config.config import get_settings

settings = get_settings()

redis = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                       encoding="utf-8", decode_responses=True, db=1)


def get_redis():
    return redis
