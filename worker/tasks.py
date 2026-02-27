import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional
import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings

from config import get_settings
from core.logger import setup_logger
from engine.browser_manager import browser_manager
from engine.page_scraper import page_scraper

logger = setup_logger("worker")


def _job_key(job_id: str) -> str:
    return f"job:{job_id}"


def _results_key(job_id: str) -> str:
    return f"job:{job_id}:results"


async def update_job_status(
    redis_client: redis.Redis,
    job_id: str,
    status: str,
    increment_completed: int = 0,
    increment_failed: int = 0,
    error: Optional[str] = None,
):
    update_data = {"status": status}
    
    if status == "running" and not await redis_client.hget(_job_key(job_id), "started_at"):
        update_data["started_at"] = datetime.utcnow().isoformat()
    
    if increment_completed:
        update_data["completed"] = increment_completed
    if increment_failed:
        update_data["failed"] = increment_failed
    if error:
        update_data["error"] = error
    
    await redis_client.hset(_job_key(job_id), mapping=update_data)


async def scrape_task(ctx: Dict[str, Any], job_id: str, url: str, request_data: Dict[str, Any]):
    redis_settings = RedisSettings(
        host=get_settings().redis_host,
        port=get_settings().redis_port,
        db=get_settings().redis_db,
        password=get_settings().redis_password,
    )
    redis_client = await redis_settings.create_redis()
    
    try:
        await update_job_status(redis_client, job_id, "running")
        
        result = await page_scraper.scrape(
            url=url,
            mode=request_data.get("mode", "full"),
            wait_for=request_data.get("wait_for"),
            timeout=request_data.get("timeout"),
            proxy=request_data.get("proxy"),
            headers=request_data.get("headers"),
            extraction_schema=json.loads(request_data["extraction_schema"])
            if request_data.get("extraction_schema")
            else None,
            extraction_prompt=request_data.get("extraction_prompt"),
        )
        
        result_dict = {
            "url": result.url,
            "success": result.success,
            "data": result.data,
            "markdown": result.markdown,
            "html": result.html if request_data.get("mode") == "html" else None,
            "error": result.error,
            "extracted_at": datetime.utcnow().isoformat(),
            "duration_ms": result.duration_ms,
        }
        
        await redis_client.rpush(_results_key(job_id), json.dumps(result_dict))
        
        if result.success:
            await update_job_status(redis_client, job_id, "running", increment_completed=1)
        else:
            await update_job_status(redis_client, job_id, "running", increment_failed=1)
        
        job_data = await redis_client.hgetall(_job_key(job_id))
        total = int(job_data.get("total", 0))
        completed = int(job_data.get("completed", 0))
        failed = int(job_data.get("failed", 0))
        
        if completed + failed >= total:
            final_status = "completed" if failed == 0 else "partial" if completed > 0 else "failed"
            await update_job_status(
                redis_client,
                job_id,
                final_status,
                error=None if final_status != "failed" else "All tasks failed",
            )
            await redis_client.hset(
                _job_key(job_id),
                "completed_at",
                datetime.utcnow().isoformat(),
            )
        
        return {"success": result.success, "url": url}
        
    except Exception as e:
        logger.error(f"Task failed for {url}: {e}")
        await update_job_status(redis_client, job_id, "running", increment_failed=1)
        await update_job_status(redis_client, job_id, "failed", error=str(e))
        raise
        
    finally:
        await redis_client.close()


async def startup(ctx):
    logger.info("Worker starting up...")
    await browser_manager.initialize()
    logger.info("Browser manager initialized")


async def shutdown(ctx):
    logger.info("Worker shutting down...")
    await browser_manager.close()
    logger.info("Browser manager closed")


class WorkerSettings:
    functions = [scrape_task]
    on_startup = startup
    on_shutdown = shutdown
    
    redis_settings = RedisSettings(
        host=get_settings().redis_host,
        port=get_settings().redis_port,
        db=get_settings().redis_db,
        password=get_settings().redis_password,
    )
    
    max_jobs = get_settings().worker_concurrency
    keep_job_results = 3600


async def main():
    from worker.config import WorkerSettings as WS
    from arq.worker import Worker
    
    worker = Worker.from_settings(WS)
    await worker.async_run()


if __name__ == "__main__":
    asyncio.run(main())
