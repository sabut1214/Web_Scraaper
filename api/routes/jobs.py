from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import redis.asyncio as redis

from config import get_settings
from schemas import JobListResponse, JobStatusResponse, JobStatus, JobProgress
from core.redis import get_redis
from core.exceptions import JobNotFoundException

router = APIRouter(prefix="/jobs", tags=["jobs"])
settings = get_settings()


def _job_key(job_id: str) -> str:
    return f"job:{job_id}"


async def _get_all_jobs(
    redis_client: redis.Redis,
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None,
) -> tuple[list[dict], int]:
    pattern = "job:*"
    keys = []
    cursor = 0
    
    while True:
        cursor, found_keys = await redis_client.scan(cursor, match=pattern, count=100)
        keys.extend(found_keys)
        if cursor == 0:
            break
    
    job_ids = list(set(k.replace("job:", "").replace(":results", "") for k in keys if ":results" not in k))
    job_ids = sorted(job_ids, reverse=True)
    
    if status_filter:
        filtered = []
        for jid in job_ids:
            job_data = await redis_client.hgetall(_job_key(jid))
            if job_data and job_data.get("status") == status_filter:
                filtered.append(job_data)
        jobs = filtered
    else:
        jobs = []
        for jid in job_ids:
            job_data = await redis_client.hgetall(_job_key(jid))
            if job_data:
                jobs.append(job_data)
    
    total = len(jobs)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_jobs = jobs[start:end]
    
    return paginated_jobs, total


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    redis_client: redis.Redis = Depends(get_redis),
):
    jobs_data, total = await _get_all_jobs(redis_client, page, page_size, status)
    
    jobs = []
    for job_data in jobs_data:
        total_count = int(job_data.get("total", 0))
        completed = int(job_data.get("completed", 0))
        failed = int(job_data.get("failed", 0))
        progress_percent = ((completed + failed) / total_count * 100) if total_count > 0 else 0.0
        
        jobs.append(JobStatusResponse(
            job_id=job_data["job_id"],
            status=JobStatus(job_data["status"]),
            created_at=datetime.fromisoformat(job_data["created_at"]),
            progress=JobProgress(
                total=total_count,
                completed=completed,
                failed=failed,
                progress_percent=progress_percent,
            ),
        ))
    
    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    redis_client: redis.Redis = Depends(get_redis),
):
    job_key = _job_key(job_id)
    results_key = f"job:{job_id}:results"
    
    exists = await redis_client.exists(job_key)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    await redis_client.delete(job_key, results_key)
    
    return {"deleted": True, "job_id": job_id}
