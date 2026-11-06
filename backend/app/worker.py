import os
import signal
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.modules.apk_builder.interface import BuildRequest
from app.modules.apk_builder.manager import engine_manager
from app.modules.apk_builder.webview.engine import WebViewEngine
from app.modules.database.engine import Base, SessionLocal, engine
from app.modules.database.repositories import BuildRepository
from app.modules.job_manager.cleanup import JobCleanupManager
from app.modules.job_manager.recovery import JobRecoveryManager
from app.modules.storage.local import LocalStorage


class Worker:
    def __init__(self):
        self.worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        self.storage = LocalStorage()
        self.running = False
        self.pool = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_BUILDS)
        self.active_jobs = 0
        self.lock = threading.Lock()
        self.last_recovery_check = 0.0
        self.last_cleanup_check = 0.0

        # Ensure database tables exist
        Base.metadata.create_all(bind=engine)

        # Register default WebView engine
        engine_manager.register(WebViewEngine(storage=self.storage))

    def _execute_build_job(self, job_id: str):
        db = SessionLocal()
        stop_heartbeat = threading.Event()

        def heartbeat_loop():
            h_db = SessionLocal()
            try:
                while not stop_heartbeat.wait(timeout=5):
                    try:
                        BuildRepository.heartbeat(h_db, job_id)
                    except Exception as e:
                        logger.warning(f"Heartbeat failed for job {job_id}: {e}")
            finally:
                h_db.close()

        hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        hb_thread.start()

        try:
            job = BuildRepository.get_by_id(db, job_id)
            if not job:
                logger.error(f"Job {job_id} not found in database.")
                return

            logger.info(f"[{job_id}] Worker {self.worker_id} started execution for URL: {job.website_url}")

            # Retrieve saved icon
            icon_file = self.storage.get_file_path(job_id, "input_icon.png")
            if not icon_file or not icon_file.exists():
                # Fallback to temp workspace icon if stored there
                fallback_icon = settings.TEMP_DIR / f"{job_id}_icon.png"
                if fallback_icon.exists():
                    icon_file = fallback_icon
                else:
                    raise FileNotFoundError(f"Icon not found for build job {job_id}")

            build_engine = engine_manager.get_engine(job.engine)

            request = BuildRequest(
                build_id=job.id,
                website_url=job.website_url,
                app_name=job.app_name,
                icon_path=icon_file,
                package_name=job.package_name,
                version_code=job.version_code,
                version_name=job.version_name,
                engine=job.engine
            )

            def on_progress(step: str, pct: int):
                try:
                    p_db = SessionLocal()
                    BuildRepository.update_progress(p_db, job_id, step, pct)
                    p_db.close()
                except Exception as ex:
                    logger.warning(f"Failed to update progress: {ex}")

            result = build_engine.build(request, progress_callback=on_progress)

            if result.status == "completed":
                BuildRepository.complete_job(
                    db=db,
                    job_id=job_id,
                    apk_path=str(result.apk_path),
                    aab_path=str(result.aab_path),
                    bundle_zip_path=str(result.bundle_zip_path),
                    metadata=result.metadata
                )
                logger.info(f"[{job_id}] Successfully finished build in {result.build_duration_seconds}s")
            else:
                BuildRepository.fail_job(db=db, job_id=job_id, error_message=result.error or "Build failed")
                logger.error(f"[{job_id}] Build failed: {result.error}")

        except Exception as e:
            logger.error(f"[{job_id}] Unhandled error executing build: {e}", exc_info=True)
            try:
                BuildRepository.fail_job(db=db, job_id=job_id, error_message=str(e))
            except Exception:
                pass
        finally:
            stop_heartbeat.set()
            db.close()
            with self.lock:
                self.active_jobs -= 1

    def start(self):
        self.running = True
        logger.info(f"Worker {self.worker_id} started (max concurrent: {settings.MAX_CONCURRENT_BUILDS}).")

        while self.running:
            try:
                now = time.time()

                # Run recovery check periodically (every 30s)
                if now - self.last_recovery_check > 30:
                    r_db = SessionLocal()
                    try:
                        JobRecoveryManager.run_recovery(r_db)
                    finally:
                        r_db.close()
                    self.last_recovery_check = now

                # Run cleanup check periodically (every 300s)
                if now - self.last_cleanup_check > 300:
                    c_db = SessionLocal()
                    try:
                        JobCleanupManager.run_cleanup(c_db, self.storage)
                    finally:
                        c_db.close()
                    self.last_cleanup_check = now

                # Check if capacity is available
                with self.lock:
                    can_claim = self.active_jobs < settings.MAX_CONCURRENT_BUILDS

                if can_claim:
                    db = SessionLocal()
                    claimed_job = None
                    try:
                        claimed_job = BuildRepository.claim_next_job(db, self.worker_id)
                    finally:
                        db.close()

                    if claimed_job:
                        with self.lock:
                            self.active_jobs += 1
                        self.pool.submit(self._execute_build_job, claimed_job.id)
                        continue

                # Short poll interval
                time.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"Worker main loop error: {e}", exc_info=True)
                time.sleep(1.0)

    def stop(self):
        logger.info(f"Stopping worker {self.worker_id}...")
        self.running = False
        self.pool.shutdown(wait=True)
        logger.info("Worker stopped successfully.")


def run():
    setup_logging()
    worker = Worker()

    def handle_signal(sig, frame):
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    worker.start()


if __name__ == "__main__":
    run()

