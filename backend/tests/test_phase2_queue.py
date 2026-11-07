import datetime
import threading
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.database.engine import Base
from app.modules.database.models import BuildJob
from app.modules.database.repositories import BuildRepository, RateLimitRepository
from app.modules.job_manager.queue import JobQueue, compute_icon_hash, compute_input_hash
from app.modules.job_manager.recovery import JobRecoveryManager
from app.modules.job_manager.cleanup import JobCleanupManager
from app.modules.storage.local import LocalStorage


import tempfile
import os

def get_test_db(db_path=None):
    url = f"sqlite:///{db_path}" if db_path else "sqlite:///:memory:"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


def test_atomic_claim_no_double_claim():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        db = get_test_db(db_path)
        # Create 5 queued jobs
        for i in range(5):
            BuildRepository.create_job(
                db=db,
                job_id=f"job_{i}",
                website_url="https://example.com",
                app_name="App",
                package_name="com.example.app",
                icon_hash="iconhash",
                input_hash=f"hash_{i}"
            )
        db.close()

        claimed_jobs = []
        lock = threading.Lock()

        def worker_claim(worker_num):
            engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False, "timeout": 30})
            Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = Session()
            for _ in range(5):
                job = BuildRepository.claim_next_job(session, f"worker_{worker_num}")
                if job:
                    with lock:
                        claimed_jobs.append(job.id)
                time.sleep(0.01)
            session.close()

        threads = [threading.Thread(target=worker_claim, args=(w,)) for w in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Every job must be claimed EXACTLY ONCE
        assert len(claimed_jobs) == 5
        assert len(set(claimed_jobs)) == 5
    finally:
        pass


def test_job_enqueue_and_reuse(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "ENABLE_BUILD_CACHE", True)
    db = get_test_db()
    icon_bytes = b"fake-png-bytes-12345"

    job1, reused1 = JobQueue.enqueue(
        db=db,
        job_id="job_fresh",
        website_url="https://example.com",
        app_name="Fresh App",
        package_name="com.example.app",
        icon_bytes=icon_bytes
    )
    assert reused1 is False
    assert job1.status == "queued"

    # Complete job1
    BuildRepository.complete_job(
        db=db,
        job_id="job_fresh",
        apk_path="/path/to/apk",
        aab_path="/path/to/aab",
        bundle_zip_path="/path/to/bundle",
        metadata={"test": True}
    )

    # Enqueue identical job -> should reuse completed job1
    job2, reused2 = JobQueue.enqueue(
        db=db,
        job_id="job_second",
        website_url="https://example.com",
        app_name="Fresh App",
        package_name="com.example.app",
        icon_bytes=icon_bytes
    )
    assert reused2 is True
    assert job2.id == "job_fresh"
    assert job2.status == "completed"
    db.close()


def test_job_recovery_stuck_heartbeat():
    db = get_test_db()
    # Create stuck job
    job = BuildRepository.create_job(
        db=db,
        job_id="stuck_job",
        website_url="https://example.com",
        app_name="Stuck",
        package_name="com.example.stuck",
        icon_hash="iconhash",
        input_hash="hash_stuck"
    )
    # Claim it
    claimed = BuildRepository.claim_next_job(db, "worker_dead")
    assert claimed is not None
    assert claimed.status == "processing"

    # Simulate heartbeat expired 5 minutes ago
    claimed.heartbeat_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=300)
    db.commit()

    reaped = BuildRepository.reap_stuck_jobs(db, timeout_seconds=120, max_retries=2)
    assert "stuck_job" in reaped

    refreshed = BuildRepository.get_by_id(db, "stuck_job")
    # Must be re-queued on first retry
    assert refreshed.status == "queued"
    assert refreshed.retry_count == 1

    # Simulate failing again past max_retries
    refreshed.status = "processing"
    refreshed.retry_count = 2
    refreshed.heartbeat_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=300)
    db.commit()

    reaped2 = BuildRepository.reap_stuck_jobs(db, timeout_seconds=120, max_retries=2)
    assert "stuck_job" in reaped2
    failed_job = BuildRepository.get_by_id(db, "stuck_job")
    assert failed_job.status == "failed"
    db.close()


def test_rate_limit_sliding_window():
    db = get_test_db()
    ip = "192.168.1.50"
    endpoint = "POST /api/v1/builds"

    # Max 3 requests in 10 seconds
    allowed1, _ = RateLimitRepository.check_and_record(db, ip, endpoint, max_requests=3, window_seconds=10)
    allowed2, _ = RateLimitRepository.check_and_record(db, ip, endpoint, max_requests=3, window_seconds=10)
    allowed3, _ = RateLimitRepository.check_and_record(db, ip, endpoint, max_requests=3, window_seconds=10)
    allowed4, retry_after = RateLimitRepository.check_and_record(db, ip, endpoint, max_requests=3, window_seconds=10)

    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is True
    assert allowed4 is False
    assert retry_after > 0
    db.close()
