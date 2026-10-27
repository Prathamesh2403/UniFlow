"""Async Redis client singleton for caching."""
import os
import logging
import redis.asyncio as redis
from core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    _client: redis.Redis | None = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._client is None:
            url = settings.REDIS_URL or os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
            masked_url = url.split("@")[-1] if "@" in url else url
            logger.info("Connecting to Redis at %s", masked_url)
            cls._client = redis.from_url(url, decode_responses=True)
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            try:
                await cls._client.close()
            except Exception:
                pass
            cls._client = None


async def get_redis():
    return await RedisManager.get_client()
