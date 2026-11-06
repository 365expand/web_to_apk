from fastapi import APIRouter
from app.core.config import settings
from app.modules.apk_builder.manager import engine_manager

router = APIRouter(prefix="/engines", tags=["Engines"])


@router.get("")
def get_engines():
    return {
        "default": settings.DEFAULT_BUILD_ENGINE,
        "enabled": engine_manager.list_enabled_engines()
    }

