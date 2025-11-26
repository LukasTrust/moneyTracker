from typing import Optional
from app.database import SessionLocal
from app.models.background_job import BackgroundJob
from datetime import datetime
from app.utils import get_logger

logger = get_logger(__name__)


class JobService:
    @staticmethod
    def create_job(db, task_type: str, account_id: Optional[int] = None, import_id: Optional[int] = None, meta: Optional[str] = None) -> BackgroundJob:
        job = BackgroundJob(
            task_type=task_type,
            status="queued",
            account_id=account_id,
            import_id=import_id,
            meta=meta,
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info("Created job", extra={"job_id": getattr(job, 'id', None), "task_type": task_type, "account_id": account_id, "import_id": import_id})
        return job

    @staticmethod
    def update_status(db, job_id: int, status: str, started: bool = False, finished: bool = False):
        job = db.query(BackgroundJob).get(job_id)
        if not job:
            return None
        job.status = status
        if started:
            job.started_at = datetime.utcnow()
        if finished:
            job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        logger.info("Updated job status", extra={"job_id": job_id, "status": status})
        return job

    @staticmethod
    def get_job(db, job_id: int):
        return db.query(BackgroundJob).get(job_id)
