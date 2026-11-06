import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
)
from app.modules.database.engine import Base


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class BuildJob(Base):
    __tablename__ = "build_jobs"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)  # Nullable for anonymous builds
    ip_address = Column(String(64), nullable=True, index=True)
    input_hash = Column(String(64), nullable=False, index=True)

    engine = Column(String(32), default="webview", nullable=False)
    website_url = Column(String(2048), nullable=False)
    app_name = Column(String(128), nullable=False)
    package_name = Column(String(150), nullable=False, index=True)
    version_code = Column(Integer, default=1, nullable=False)
    version_name = Column(String(32), default="1.0.0", nullable=False)
    icon_hash = Column(String(64), nullable=False)

    # Status: queued, processing, completed, failed, expired
    status = Column(String(32), default="queued", index=True, nullable=False)
    # Step: validating, preparing, building, packaging, completed
    step = Column(String(32), default="validating", nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)

    # Output file paths or keys
    apk_path = Column(String(512), nullable=True)
    aab_path = Column(String(512), nullable=True)
    bundle_zip_path = Column(String(512), nullable=True)
    build_metadata = Column(JSON, nullable=True)

    retry_count = Column(Integer, default=0, nullable=False)
    worker_id = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    heartbeat_at = Column(DateTime, nullable=True, index=True)


class RateLimitRecord(Base):
    __tablename__ = "rate_limit_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(64), index=True, nullable=False)
    endpoint = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
