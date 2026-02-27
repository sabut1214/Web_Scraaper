from datetime import datetime
from typing import List
import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
import redis.asyncio as redis

from config import get_settings
from schemas import (
    ScrapeRequest,
    BatchScrapeRequest,
    JobStatusResponse,
    JobStatus,
    JobProgress,
    JobResultResponse,
    JobListResponse,
    ScrapeResultItem,
    JobSummary,
)
from core.redis import get_redis
from core.exceptions import JobNotFoundException

router = APIRouter(prefix="/scrape", tags=["scrape"])
settings = get_settings()


def _job_key(job_id: str) -> str:
    return f"job:{job_id}"


def _results_key(job_id: str) -> str:
    return f"job:{job_id}:results"


def _queue_key() -> str:
    return "queue:scrape_tasks"


async def _create_job(
    redis_client: redis.Redis,
    urls: List[str],
    request_data: dict,
    priority: int = 5,
) -> str:
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "status": JobStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
        "total": len(urls),
        "completed": 0,
        "failed": 0,
        "request": json.dumps(request_data),
    }
    
    await redis_client.hset(_job_key(job_id), mapping=job_data)
    await redis_client.expire(_job_key(job_id), 86400 * 7)
    
    for url in urls:
        task_data = {
            "job_id": job_id,
            "url": url,
            **request_data,
        }
        await redis_client.zadd(
            _queue_key(),
            {json.dumps(task_data): priority},
        )
    
    return job_id


async def _get_job_status(redis_client: redis.Redis, job_id: str) -> dict:
    job_data = await redis_client.hgetall(_job_key(job_id))
    if not job_data:
        raise JobNotFoundException(f"Job {job_id} not found")
    return job_data


async def _get_job_results(redis_client: redis.Redis, job_id: str) -> List[dict]:
    results = await redis_client.lrange(_results_key(job_id), 0, -1)
    return [json.loads(r) for r in results]


@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_scrape_job(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    redis_client: redis.Redis = Depends(get_redis),
):
    job_id = await _create_job(
        redis_client,
        urls=[str(request.url)],
        request_data={
            "mode": request.mode.value,
            "extraction_schema": json.dumps(request.extraction_schema) if request.extraction_schema else None,
            "extraction_prompt": request.extraction_prompt,
            "proxy": request.proxy.model_dump() if request.proxy else None,
            "headers": request.headers,
            "wait_for": request.wait_for,
            "timeout": request.timeout,
        },
        priority=request.priority,
    )
    
    job_data = await _get_job_status(redis_client, job_id)
    
    return JobStatusResponse(
        job_id=job_data["job_id"],
        status=JobStatus(job_data["status"]),
        created_at=datetime.fromisoformat(job_data["created_at"]),
        progress=JobProgress(
            total=int(job_data["total"]),
            completed=int(job_data["completed"]),
            failed=int(job_data["failed"]),
            progress_percent=0.0,
        ),
    )


@router.post("/batch", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_batch_scrape_job(
    request: BatchScrapeRequest,
    redis_client: redis.Redis = Depends(get_redis),
):
    job_id = await _create_job(
        redis_client,
        urls=[str(u) for u in request.urls],
        request_data={
            "mode": request.mode.value,
            "extraction_schema": json.dumps(request.extraction_schema) if request.extraction_schema else None,
            "extraction_prompt": request.extraction_prompt,
            "proxy": request.proxy.model_dump() if request.proxy else None,
            "headers": request.headers,
            "wait_for": request.wait_for,
            "timeout": request.timeout,
        },
        priority=request.priority,
    )
    
    job_data = await _get_job_status(redis_client, job_id)
    
    return JobStatusResponse(
        job_id=job_data["job_id"],
        status=JobStatus(job_data["status"]),
        created_at=datetime.fromisoformat(job_data["created_at"]),
        progress=JobProgress(
            total=int(job_data["total"]),
            completed=int(job_data["completed"]),
            failed=int(job_data["failed"]),
            progress_percent=0.0,
        ),
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    redis_client: redis.Redis = Depends(get_redis),
):
    try:
        job_data = await _get_job_status(redis_client, job_id)
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    total = int(job_data.get("total", 0))
    completed = int(job_data.get("completed", 0))
    failed = int(job_data.get("failed", 0))
    progress_percent = ((completed + failed) / total * 100) if total > 0 else 0.0
    
    started_at = datetime.fromisoformat(job_data["started_at"]) if job_data.get("started_at") else None
    completed_at = datetime.fromisoformat(job_data["completed_at"]) if job_data.get("completed_at") else None
    
    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus(job_data["status"]),
        created_at=datetime.fromisoformat(job_data["created_at"]),
        started_at=started_at,
        completed_at=completed_at,
        progress=JobProgress(
            total=total,
            completed=completed,
            failed=failed,
            progress_percent=progress_percent,
        ),
        error=job_data.get("error"),
    )


@router.get("/results/{job_id}", response_model=JobResultResponse)
async def get_job_results(
    job_id: str,
    redis_client: redis.Redis = Depends(get_redis),
):
    try:
        job_data = await _get_job_status(redis_client, job_id)
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    results_raw = await _get_job_results(redis_client, job_id)
    results = [ScrapeResultItem(**r) for r in results_raw]
    
    successful = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    
    completed_at = datetime.fromisoformat(job_data["completed_at"]) if job_data.get("completed_at") else None
    
    return JobResultResponse(
        job_id=job_id,
        status=JobStatus(job_data["status"]),
        results=results,
        summary=JobSummary(
            total=len(results),
            successful=successful,
            failed=failed,
        ),
        created_at=datetime.fromisoformat(job_data["created_at"]),
        completed_at=completed_at,
    )
