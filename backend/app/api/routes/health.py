from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.apk_builder.manager import engine_manager
from app.modules.database.engine import get_db
from app.modules.database.repositories import BuildRepository

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def get_health(db: Session = Depends(get_db)):
    queued = BuildRepository.count_queued_jobs(db)
    processing = BuildRepository.count_processing_jobs(db)

    return {
        "status": "healthy",
        "queue": {
            "queued_jobs": queued,
            "processing_jobs": processing,
            "max_concurrent": settings.MAX_CONCURRENT_BUILDS,
            "max_queue_length": settings.MAX_QUEUE_LENGTH,
        },
        "engines": {
            "default": settings.DEFAULT_BUILD_ENGINE,
            "enabled": engine_manager.list_enabled_engines(),
        },
        "retention_hours": settings.APK_RETENTION_HOURS
    }

