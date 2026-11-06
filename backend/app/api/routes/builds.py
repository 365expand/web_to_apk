import io
import secrets
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import User, get_current_user
from app.core.config import settings
from app.core.logging import logger
from app.core.ratelimit import enforce_build_rate_limit, enforce_lightweight_rate_limit
from app.core.security import SecurityValidationError, validate_and_clean_url
from app.modules.apk_builder.validators import (
    generate_package_name,
    sanitize_package_name_override,
    validate_package_name,
    validate_version_code,
    validate_version_name,
)
from app.modules.database.engine import get_db
from app.modules.icon_processor.processor import IconValidationError, validate_and_load_icon
from app.modules.job_manager.queue import JobQueue
from app.modules.storage.local import LocalStorage

router = APIRouter(prefix="/builds", tags=["Builds"])
storage = LocalStorage()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_build(
    request: Request,
    website_url: str = Form(...),
    app_name: str = Form(...),
    icon: UploadFile = File(...),
    package_name: Optional[str] = Form(None),
    version_code: Optional[int] = Form(1),
    version_name: Optional[str] = Form("1.0.0"),
    engine: str = Form("webview"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Abuse & Rate limit enforcement
    client_ip = enforce_build_rate_limit(request, db)

    # 2. SSRF, URL validation and credential stripping
    try:
        clean_url = validate_and_clean_url(website_url)
    except SecurityValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Website URL: {str(e)}"
        )

    # 3. App Name validation
    app_name_clean = app_name.strip()
    if not app_name_clean or len(app_name_clean) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App name must be between 1 and 100 characters."
        )

    # 4. Package name validation / generation
    if package_name and package_name.strip():
        pkg_to_use = sanitize_package_name_override(package_name)
        is_valid, pkg_err = validate_package_name(pkg_to_use)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid package name: {pkg_err}"
            )
    else:
        pkg_to_use = generate_package_name(clean_url)
        is_valid, pkg_err = validate_package_name(pkg_to_use)
        if not is_valid:
            pkg_to_use = "com.webtoapk.app"

    # 5. Version code and name validation
    try:
        v_code = validate_version_code(version_code)
        v_name = validate_version_name(version_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 6. Icon validation (decoding, decompression bomb protection, 1:1 aspect ratio)
    try:
        icon_bytes = await icon.read()
        if len(icon_bytes) > settings.MAX_ICON_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Icon file exceeds {settings.MAX_ICON_SIZE_MB}MB size limit."
            )
        # Validate using Pillow
        validate_and_load_icon(icon_bytes, max_size_mb=settings.MAX_ICON_SIZE_MB)
    except IconValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid icon: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to process icon: {str(e)}")

    # 7. Generate unguessable build ID
    build_id = secrets.token_urlsafe(24)

    # 8. Store icon for worker
    temp_icon_path = settings.TEMP_DIR / f"{build_id}_icon.png"
    temp_icon_path.write_bytes(icon_bytes)
    storage.save_file(build_id, "input_icon.png", temp_icon_path)

    # 9. Enqueue job (or reuse existing matching build within retention window)
    job, was_reused = JobQueue.enqueue(
        db=db,
        job_id=build_id,
        website_url=clean_url,
        app_name=app_name_clean,
        package_name=pkg_to_use,
        icon_bytes=icon_bytes,
        version_code=v_code,
        version_name=v_name,
        engine=engine,
        user_id=current_user.user_id,
        ip_address=client_ip
    )

    info = JobQueue.get_job_info(db, job.id)
    if not info:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve job state.")

    info["reused_existing"] = was_reused
    logger.info(f"Build job {job.id} registered (reused={was_reused}, status={job.status})")
    return info


@router.get("/{build_id}")
def get_build_status(
    build_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    enforce_lightweight_rate_limit(request, db, endpoint="GET /api/v1/builds/{id}")
    info = JobQueue.get_job_info(db, build_id)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build '{build_id}' was not found or has expired."
        )
    return info

