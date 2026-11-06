from typing import List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.modules.database.repositories import BuildRepository


class JobRecoveryManager:
    @staticmethod
    def run_recovery(db: Session) -> List[str]:
        reaped_ids = BuildRepository.reap_stuck_jobs(
            db=db,
            timeout_seconds=settings.HEARTBEAT_TIMEOUT_SECONDS,
            max_retries=2
        )
        if reaped_ids:
            logger.warning(f"Recovery manager processed stuck jobs: {reaped_ids}")
        return reaped_ids

