import hashlib
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.database.models import BuildJob
from app.modules.database.repositories import BuildRepository


def compute_icon_hash(icon_bytes: bytes) -> str:
    return hashlib.sha256(icon_bytes).hexdigest()


def compute_input_hash(
    url: str,
    name: str,
    package: str,
    icon_hash: str,
    version_code: int,
    version_name: str
) -> str:
    raw = f"{url.strip()}|{name.strip()}|{package.strip()}|{icon_hash}|{version_code}|{version_name.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class JobQueue:
    @staticmethod
    def enqueue(
        db: Session,
        job_id: str,
        website_url: str,
        app_name: str,
        package_name: str,
        icon_bytes: bytes,
        version_code: int = 1,
        version_name: str = "1.0.0",
        engine: str = "webview",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[BuildJob, bool]:
        """
        Enqueues a build job or reuses an existing valid build if matching input_hash
        was already completed within the retention window.
        Returns (job, was_reused).
        """
        icon_hash = compute_icon_hash(icon_bytes)
        input_hash = compute_input_hash(
            url=website_url,
            name=app_name,
            package=package_name,
            icon_hash=icon_hash,
            version_code=version_code,
            version_name=version_name
        )

        # Check for reuse if build cache is enabled
        if settings.ENABLE_BUILD_CACHE:
            existing = BuildRepository.find_active_by_input_hash(
                db=db,
                input_hash=input_hash,
                retention_hours=settings.APK_RETENTION_HOURS
            )
            if existing:
                return existing, True

        # Create new queued job
        job = BuildRepository.create_job(
            db=db,
            job_id=job_id,
            website_url=website_url,
            app_name=app_name,
            package_name=package_name,
            icon_hash=icon_hash,
            input_hash=input_hash,
            version_code=version_code,
            version_name=version_name,
            engine=engine,
            user_id=user_id,
            ip_address=ip_address
        )
        return job, False

    @staticmethod
    def get_job_info(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
        job = BuildRepository.get_by_id(db, job_id)
        if not job:
            return None

        position, eta = BuildRepository.get_queue_position_and_eta(db, job_id)
        return {
            "id": job.id,
            "engine": job.engine,
            "website_url": job.website_url,
            "app_name": job.app_name,
            "package_name": job.package_name,
            "version_code": job.version_code,
            "version_name": job.version_name,
            "status": job.status,
            "step": job.step,
            "progress": job.progress,
            "error": job.error,
            "queue_position": position,
            "estimated_wait_seconds": eta,
            "has_apk": bool(job.apk_path),
            "has_aab": bool(job.aab_path),
            "has_bundle": bool(job.bundle_zip_path),
            "metadata": job.build_metadata or {},
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
