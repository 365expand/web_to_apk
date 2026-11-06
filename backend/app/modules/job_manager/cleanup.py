from typing import List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.modules.database.repositories import BuildRepository
from app.modules.storage.interface import StorageInterface


class JobCleanupManager:
    @staticmethod
    def run_cleanup(db: Session, storage: StorageInterface) -> List[str]:
        expired_jobs = BuildRepository.get_expired_jobs(
            db=db,
            retention_hours=settings.APK_RETENTION_HOURS
        )
        cleaned_ids = []
        for job in expired_jobs:
            logger.info(f"Cleaning up expired build artifacts for job: {job.id}")
            storage.delete_build_files(job.id)
            BuildRepository.mark_expired(db, job.id)
            cleaned_ids.append(job.id)

        return cleaned_ids

