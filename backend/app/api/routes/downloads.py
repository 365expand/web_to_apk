from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.ratelimit import enforce_lightweight_rate_limit
from app.modules.database.engine import get_db
from app.modules.database.repositories import BuildRepository
from app.modules.storage.local import LocalStorage

router = APIRouter(prefix="/builds", tags=["Downloads"])
storage = LocalStorage()


def get_verified_completed_job(build_id: str, db: Session, request: Request):
    enforce_lightweight_rate_limit(request, db, endpoint="downloads")
    job = BuildRepository.get_by_id(db, build_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build '{build_id}' was not found or has expired."
        )
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Build '{build_id}' is not ready for download (current status: {job.status})."
        )
    return job


@router.get("/{build_id}/download/apk")
def download_apk(
    build_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    job = get_verified_completed_job(build_id, db, request)
    apk_path = storage.get_file_path(build_id, "app-release.apk")
    if not apk_path or not apk_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="APK artifact file missing or expired.")

    safe_app_name = "".join(c for c in job.app_name if c.isalnum() or c in ("-", "_")).strip() or "app"
    filename = f"{safe_app_name}-release.apk"
    return FileResponse(
        path=str(apk_path),
        filename=filename,
        media_type="application/vnd.android.package-archive"
    )


@router.get("/{build_id}/download/aab")
def download_aab(
    build_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    job = get_verified_completed_job(build_id, db, request)
    aab_path = storage.get_file_path(build_id, "app-release.aab")
    if not aab_path or not aab_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AAB artifact file missing or expired.")

    safe_app_name = "".join(c for c in job.app_name if c.isalnum() or c in ("-", "_")).strip() or "app"
    filename = f"{safe_app_name}-release.aab"
    return FileResponse(
        path=str(aab_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/{build_id}/download/bundle")
def download_bundle(
    build_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    job = get_verified_completed_job(build_id, db, request)
    bundle_path = storage.get_file_path(build_id, "bundle.zip")
    if not bundle_path or not bundle_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle zip artifact missing or expired.")

    safe_app_name = "".join(c for c in job.app_name if c.isalnum() or c in ("-", "_")).strip() or "app"
    filename = f"{safe_app_name}-release-bundle.zip"
    return FileResponse(
        path=str(bundle_path),
        filename=filename,
        media_type="application/zip"
    )

