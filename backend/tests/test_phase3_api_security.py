import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.security import SecurityValidationError, validate_and_clean_url
from app.main import app
from app.modules.database.engine import Base, SessionLocal, engine
from app.modules.database.models import BuildJob, RateLimitRecord

Base.metadata.create_all(bind=engine)
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    session = SessionLocal()
    session.query(RateLimitRecord).delete()
    session.query(BuildJob).delete()
    session.commit()
    session.close()


def test_ssrf_rejects_loopback():
    with pytest.raises(SecurityValidationError, match="Access to localhost is prohibited|prohibited"):
        validate_and_clean_url("http://127.0.0.1")

    with pytest.raises(SecurityValidationError, match="Access to localhost is prohibited|prohibited"):
        validate_and_clean_url("http://localhost")


def test_ssrf_rejects_cloud_metadata():
    with pytest.raises(SecurityValidationError, match="prohibited"):
        validate_and_clean_url("http://169.254.169.254/latest/meta-data/")


def test_ssrf_rejects_private_ips():
    with pytest.raises(SecurityValidationError, match="prohibited"):
        validate_and_clean_url("http://192.168.1.1")
    with pytest.raises(SecurityValidationError, match="prohibited"):
        validate_and_clean_url("http://10.0.0.5")


def test_ssrf_rejects_non_standard_ports():
    with pytest.raises(SecurityValidationError, match="Non-standard ports"):
        validate_and_clean_url("http://example.com:8080")
    with pytest.raises(SecurityValidationError, match="Non-standard ports"):
        validate_and_clean_url("https://example.com:8443")


def test_ssrf_rejects_blocked_domains():
    with pytest.raises(SecurityValidationError, match="blocked due to security"):
        validate_and_clean_url("https://paypal-login.com/login")


def test_ssrf_allows_valid_public_domain_and_strips_credentials():
    url = "https://user:password@example.com/shop?item=1"
    clean = validate_and_clean_url(url)
    assert clean == "https://example.com/shop?item=1"
    assert "password" not in clean


def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "queue" in data
    assert "engines" in data


def test_api_engines():
    response = client.get("/api/v1/engines")
    assert response.status_code == 200
    data = response.json()
    assert "webview" in data["enabled"]
    assert data["default"] == "webview"


def test_api_create_build_validation_errors():
    # Missing fields
    res = client.post("/api/v1/builds")
    assert res.status_code == 422

    # Invalid non-square icon (both >= 192px, but not square)
    non_square = Image.new("RGBA", (300, 200), (255, 0, 0, 255))
    buf = io.BytesIO()
    non_square.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        "/api/v1/builds",
        data={"website_url": "https://example.com", "app_name": "Test App"},
        files={"icon": ("icon.png", buf, "image/png")}
    )
    assert res.status_code == 400
    assert "square aspect ratio" in res.json()["detail"].lower()


def test_api_create_build_and_status():
    # Valid 1:1 icon
    square = Image.new("RGBA", (256, 256), (33, 150, 243, 255))
    buf = io.BytesIO()
    square.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        "/api/v1/builds",
        data={
            "website_url": "https://example.com",
            "app_name": "Example App",
            "package_name": "com.exampleapp.android",
            "version_code": 2,
            "version_name": "1.2.0"
        },
        files={"icon": ("icon.png", buf, "image/png")}
    )
    assert res.status_code == 202
    data = res.json()
    assert "id" in data
    assert data["status"] in ("queued", "completed")
    assert data["version_code"] == 2
    assert data["version_name"] == "1.2.0"

    # Status endpoint
    build_id = data["id"]
    status_res = client.get(f"/api/v1/builds/{build_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["id"] == build_id
