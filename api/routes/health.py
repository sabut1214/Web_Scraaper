from fastapi import APIRouter, Depends
import redis.asyncio as redis

from config import get_settings
from schemas import HealthResponse
from core.redis import get_redis, redis_client

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


@router.get("", response_model=HealthResponse)
async def health_check(redis_client: redis.Redis = Depends(get_redis)):
    redis_connected = await redis_client.ping()
    
    return HealthResponse(
        status="healthy" if redis_connected else "degraded",
        version=settings.app_version,
        redis_connected=redis_connected,
        workers_active=0,
    )


@router.get("/ready")
async def readiness_check(redis_client: redis.Redis = Depends(get_redis)):
    await redis_client.ping()
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    return {"alive": True}
