import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.database.models import BuildJob, RateLimitRecord


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class BuildRepository:
    @staticmethod
    def create_job(
        db: Session,
        job_id: str,
        website_url: str,
        app_name: str,
        package_name: str,
        icon_hash: str,
        input_hash: str,
        version_code: int = 1,
        version_name: str = "1.0.0",
        engine: str = "webview",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> BuildJob:
        job = BuildJob(
            id=job_id,
            user_id=user_id,
            ip_address=ip_address,
            input_hash=input_hash,
            engine=engine,
            website_url=website_url,
            app_name=app_name,
            package_name=package_name,
            version_code=version_code,
            version_name=version_name,
            icon_hash=icon_hash,
            status="queued",
            step="validating",
            progress=0,
            created_at=utc_now()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_by_id(db: Session, job_id: str) -> Optional[BuildJob]:
        return db.query(BuildJob).filter(BuildJob.id == job_id).first()

    @staticmethod
    def find_active_by_input_hash(db: Session, input_hash: str, retention_hours: int = 24) -> Optional[BuildJob]:
        cutoff = utc_now() - datetime.timedelta(hours=retention_hours)
        return (
            db.query(BuildJob)
            .filter(
                BuildJob.input_hash == input_hash,
                BuildJob.status == "completed",
                BuildJob.created_at >= cutoff
            )
            .order_by(BuildJob.created_at.desc())
            .first()
        )

    @staticmethod
    def count_active_jobs_for_ip(db: Session, ip_address: str) -> int:
        if not ip_address:
            return 0
        return (
            db.query(BuildJob)
            .filter(
                BuildJob.ip_address == ip_address,
                BuildJob.status.in_(["queued", "processing"])
            )
            .count()
        )

    @staticmethod
    def count_queued_jobs(db: Session) -> int:
        return db.query(BuildJob).filter(BuildJob.status == "queued").count()

    @staticmethod
    def count_processing_jobs(db: Session) -> int:
        return db.query(BuildJob).filter(BuildJob.status == "processing").count()

    @staticmethod
    def claim_next_job(db: Session, worker_id: str) -> Optional[BuildJob]:
        """
        Atomically claims the oldest queued job using BEGIN IMMEDIATE in SQLite.
        Guarantees that multiple concurrent workers never claim the same job.
        """
        try:
            if db.bind and db.bind.dialect.name == "sqlite":
                # Acquire exclusive write lock immediately
                db.execute(text("BEGIN IMMEDIATE"))

            candidate = (
                db.query(BuildJob)
                .filter(BuildJob.status == "queued")
                .order_by(BuildJob.created_at.asc())
                .first()
            )

            if not candidate:
                db.commit()
                return None

            now = utc_now()
            candidate.status = "processing"
            candidate.step = "preparing"
            candidate.progress = 15
            candidate.worker_id = worker_id
            candidate.started_at = now
            candidate.heartbeat_at = now

            db.commit()
            db.refresh(candidate)
            return candidate
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def update_progress(db: Session, job_id: str, step: str, progress: int) -> None:
        db.query(BuildJob).filter(BuildJob.id == job_id).update({
            BuildJob.step: step,
            BuildJob.progress: progress,
            BuildJob.heartbeat_at: utc_now()
        })
        db.commit()

    @staticmethod
    def heartbeat(db: Session, job_id: str) -> None:
        db.query(BuildJob).filter(BuildJob.id == job_id).update({
            BuildJob.heartbeat_at: utc_now()
        })
        db.commit()

    @staticmethod
    def complete_job(
        db: Session,
        job_id: str,
        apk_path: str,
        aab_path: str,
        bundle_zip_path: str,
        metadata: Dict[str, Any]
    ) -> None:
        now = utc_now()
        db.query(BuildJob).filter(BuildJob.id == job_id).update({
            BuildJob.status: "completed",
            BuildJob.step: "completed",
            BuildJob.progress: 100,
            BuildJob.apk_path: str(apk_path),
            BuildJob.aab_path: str(aab_path),
            BuildJob.bundle_zip_path: str(bundle_zip_path),
            BuildJob.build_metadata: metadata,
            BuildJob.completed_at: now,
            BuildJob.heartbeat_at: now
        })
        db.commit()

    @staticmethod
    def fail_job(db: Session, job_id: str, error_message: str) -> None:
        db.query(BuildJob).filter(BuildJob.id == job_id).update({
            BuildJob.status: "failed",
            BuildJob.error: error_message,
            BuildJob.completed_at: utc_now()
        })
        db.commit()

    @staticmethod
    def get_queue_position_and_eta(db: Session, job_id: str) -> Tuple[int, int]:
        job = db.query(BuildJob).filter(BuildJob.id == job_id).first()
        if not job or job.status != "queued":
            return 0, 0

        position = (
            db.query(BuildJob)
            .filter(
                BuildJob.status == "queued",
                BuildJob.created_at < job.created_at
            )
            .count()
        ) + 1

        # Rough ETA estimation: ~60 seconds per build ahead in queue
        eta_seconds = position * 60
        return position, eta_seconds

    @staticmethod
    def get_expired_jobs(db: Session, retention_hours: int = 24) -> List[BuildJob]:
        cutoff = utc_now() - datetime.timedelta(hours=retention_hours)
        return (
            db.query(BuildJob)
            .filter(
                BuildJob.created_at < cutoff,
                BuildJob.status.in_(["completed", "failed"])
            )
            .all()
        )

    @staticmethod
    def mark_expired(db: Session, job_id: str) -> None:
        db.query(BuildJob).filter(BuildJob.id == job_id).update({
            BuildJob.status: "expired",
            BuildJob.apk_path: None,
            BuildJob.aab_path: None,
            BuildJob.bundle_zip_path: None
        })
        db.commit()

    @staticmethod
    def reap_stuck_jobs(db: Session, timeout_seconds: int = 120, max_retries: int = 2) -> List[str]:
        """
        Finds jobs stuck in 'processing' whose worker stopped sending heartbeats.
        Re-queues them if within retry limit, or marks failed.
        """
        cutoff = utc_now() - datetime.timedelta(seconds=timeout_seconds)
        stuck_jobs = (
            db.query(BuildJob)
            .filter(
                BuildJob.status == "processing",
                BuildJob.heartbeat_at < cutoff
            )
            .all()
        )

        reaped = []
        for job in stuck_jobs:
            if job.retry_count < max_retries:
                job.status = "queued"
                job.retry_count += 1
                job.worker_id = None
                job.step = "re-queued"
                job.error = f"Worker heartbeat timeout. Re-queuing (attempt {job.retry_count}/{max_retries})."
            else:
                job.status = "failed"
                job.error = "Build worker crashed or heartbeat timed out permanently."
                job.completed_at = utc_now()
            reaped.append(job.id)

        db.commit()
        return reaped


class RateLimitRepository:
    @staticmethod
    def check_and_record(
        db: Session,
        ip_address: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Sliding-window rate limiter stored in SQLite.
        Returns (is_allowed, retry_after_seconds).
        """
        now = utc_now()
        window_start = now - datetime.timedelta(seconds=window_seconds)

        # Clean old records for this IP/endpoint
        db.query(RateLimitRecord).filter(
            RateLimitRecord.ip_address == ip_address,
            RateLimitRecord.endpoint == endpoint,
            RateLimitRecord.timestamp < window_start
        ).delete(synchronize_session=False)

        count = (
            db.query(RateLimitRecord)
            .filter(
                RateLimitRecord.ip_address == ip_address,
                RateLimitRecord.endpoint == endpoint,
                RateLimitRecord.timestamp >= window_start
            )
            .count()
        )

        if count >= max_requests:
            # Find earliest record in window to calculate retry_after
            oldest = (
                db.query(RateLimitRecord)
                .filter(
                    RateLimitRecord.ip_address == ip_address,
                    RateLimitRecord.endpoint == endpoint,
                    RateLimitRecord.timestamp >= window_start
                )
                .order_by(RateLimitRecord.timestamp.asc())
                .first()
            )
            retry_after = 60
            if oldest:
                elapsed = (now - oldest.timestamp).total_seconds()
                retry_after = max(1, int(window_seconds - elapsed))
            db.commit()
            return False, retry_after

        # Record this request
        new_record = RateLimitRecord(
            ip_address=ip_address,
            endpoint=endpoint,
            timestamp=now
        )
        db.add(new_record)
        db.commit()
        return True, 0
