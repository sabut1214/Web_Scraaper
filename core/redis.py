from datetime import datetime
from typing import Any, Dict, Optional
import json
import redis.asyncio as redis
from config import get_settings


class RedisClient:
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                password=self.settings.redis_password,
                decode_responses=True,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def ping(self) -> bool:
        client = await self.get_client()
        try:
            await client.ping()
            return True
        except Exception:
            return False


redis_client = RedisClient()


async def get_redis() -> redis.Redis:
    return await redis_client.get_client()
