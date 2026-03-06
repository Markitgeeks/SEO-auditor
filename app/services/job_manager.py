import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str
    job_type: str  # "sitemap_export" | "tag_scan" | "competitor_research"
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0  # 0.0 - 1.0
    progress_message: str = ""
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    result_path: Optional[str] = None  # path to generated XLSX
    result_data: Optional[dict] = None  # summary stats
    error_message: Optional[str] = None
    errors: list[dict] = field(default_factory=list)
    created_at: str = ""
    completed_at: Optional[str] = None
    brand_id: Optional[str] = None


_jobs: dict[str, Job] = {}
_MAX_JOBS = 50


def create_job(job_type: str, brand_id: str = None) -> Job:
    if len(_jobs) >= _MAX_JOBS:
        oldest = min(_jobs.values(), key=lambda j: j.created_at)
        del _jobs[oldest.id]
    job = Job(
        id=str(uuid.uuid4()),
        job_type=job_type,
        brand_id=brand_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _jobs[job.id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _jobs.get(job_id)


def update_job(job_id: str, **kwargs):
    job = _jobs.get(job_id)
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
