from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class ScrapeMode(str, Enum):
    HTML = "html"
    MARKUP = "markup"
    EXTRACTION = "extraction"
    FULL = "full"


class ProxyConfig(BaseModel):
    url: str
    username: Optional[str] = None
    password: Optional[str] = None


class ScrapeRequest(BaseModel):
    url: HttpUrl
    mode: ScrapeMode = ScrapeMode.EXTRACTION
    extraction_schema: Optional[Dict[str, Any]] = None
    extraction_prompt: Optional[str] = None
    proxy: Optional[ProxyConfig] = None
    headers: Optional[Dict[str, str]] = None
    wait_for: Optional[str] = None
    timeout: Optional[int] = None
    priority: int = 5


class BatchScrapeRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., min_length=1, max_length=1000)
    mode: ScrapeMode = ScrapeMode.EXTRACTION
    extraction_schema: Optional[Dict[str, Any]] = None
    extraction_prompt: Optional[str] = None
    proxy: Optional[ProxyConfig] = None
    headers: Optional[Dict[str, str]] = None
    wait_for: Optional[str] = None
    timeout: Optional[int] = None
    priority: int = 5


class ScrapeResultItem(BaseModel):
    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    error: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None


class JobProgress(BaseModel):
    total: int
    completed: int
    failed: int
    progress_percent: float = Field(ge=0.0, le=100.0)


class JobSummary(BaseModel):
    total: int
    successful: int
    failed: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: JobProgress
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    results: List[ScrapeResultItem] = Field(default_factory=list)
    summary: JobSummary
    created_at: datetime
    completed_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    jobs: List[JobStatusResponse]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    redis_connected: bool
    workers_active: int = 0
