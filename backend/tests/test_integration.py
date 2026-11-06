import io
import subprocess
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import settings
from app.main import app
from app.modules.apk_builder.interface import BuildRequest
from app.modules.apk_builder.webview.engine import WebViewEngine
from app.modules.database.engine import Base, SessionLocal, engine
from app.modules.database.repositories import BuildRepository
from app.modules.storage.local import LocalStorage

client = TestClient(app)


@pytest.mark.integration
def test_full_pipeline_apk_and_aab():
    Base.metadata.create_all(bind=engine)
    storage = LocalStorage()
    db = SessionLocal()
    
    # Clean rate limits for integration test
    from app.modules.database.models import RateLimitRecord, BuildJob
    db.query(RateLimitRecord).delete()
    db.query(BuildJob).delete()
    db.commit()

    # Generate 1:1 square icon
    icon_img = Image.new("RGBA", (256, 256), (33, 150, 243, 255))
    buf = io.BytesIO()
    icon_img.save(buf, format="PNG")
    icon_bytes = buf.getvalue()

    # 1. Test POST /api/v1/builds
    buf.seek(0)
    res = client.post(
        "/api/v1/builds",
        data={
            "website_url": "https://example.org",
            "app_name": "Integration App",
            "package_name": "org.example.integration",
            "version_code": 1,
            "version_name": "1.0.0"
        },
        files={"icon": ("icon.png", buf, "image/png")}
    )
    assert res.status_code == 202
    build_id = res.json()["id"]

    # 2. Execute build using WebViewEngine
    builder = WebViewEngine(storage=storage)
    req = BuildRequest(
        build_id=build_id,
        website_url="https://example.org",
        app_name="Integration App",
        icon_bytes=icon_bytes,
        package_name="org.example.integration",
        version_code=1,
        version_name="1.0.0"
    )

    result = builder.build(req)
    assert result.status == "completed"
    assert result.apk_path is not None
    assert result.aab_path is not None
    assert result.apk_path.exists()
    assert result.aab_path.exists()
    assert result.aab_path.stat().st_size > 0

    # 3. Verify APK signature with apksigner
    apksigner_bin = settings.resolve_apksigner()
    verify_res = subprocess.run(
        [apksigner_bin, "verify", "--verbose", str(result.apk_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    assert verify_res.returncode == 0
    assert "Verified using v2 scheme (APK Signature Scheme v2): true" in verify_res.stdout

    # 4. Mark job completed in database
    BuildRepository.complete_job(
        db=db,
        job_id=build_id,
        apk_path=str(result.apk_path),
        aab_path=str(result.aab_path),
        bundle_zip_path=str(result.bundle_zip_path),
        metadata=result.metadata
    )

    # 5. Test download endpoints
    apk_res = client.get(f"/api/v1/builds/{build_id}/download/apk")
    assert apk_res.status_code == 200
    assert apk_res.headers["content-type"] == "application/vnd.android.package-archive"

    aab_res = client.get(f"/api/v1/builds/{build_id}/download/aab")
    assert aab_res.status_code == 200

    bundle_res = client.get(f"/api/v1/builds/{build_id}/download/bundle")
    assert bundle_res.status_code == 200
    assert bundle_res.headers["content-type"] == "application/zip"

    db.close()
