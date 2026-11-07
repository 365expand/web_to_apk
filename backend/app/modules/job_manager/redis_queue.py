import json
from typing import Optional
from app.core.config import settings
from app.core.logging import logger

_redis_client = None
_redis_checked = False


def get_redis_client():
    global _redis_client, _redis_checked
    if _redis_checked and _redis_client is None:
        return None

    if _redis_client is not None:
        return _redis_client

    if not settings.REDIS_URL or settings.QUEUE_BACKEND == "sqlite":
        _redis_checked = True
        return None

    try:
        import redis
        client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        _redis_checked = True
        logger.info(f"Connected to Redis queue at {settings.REDIS_URL.split('@')[-1]}")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis not available or connection failed: {e}. Falling back to SQLite WAL queue.")
        _redis_checked = True
        _redis_client = None
        return None


class RedisJobQueue:
    QUEUE_KEY = "webtoapk:jobs:queued"
    PROCESSING_KEY = "webtoapk:jobs:processing"

    @classmethod
    def push_job(cls, job_id: str) -> bool:
        client = get_redis_client()
        if not client:
            return False
        try:
            client.lpush(cls.QUEUE_KEY, job_id)
            client.publish("webtoapk:events:jobs", json.dumps({"event": "enqueued", "job_id": job_id}))
            return True
        except Exception as e:
            logger.warning(f"Failed to push job {job_id} to Redis: {e}")
            return False

    @classmethod
    def pop_job(cls, timeout: int = 1) -> Optional[str]:
        client = get_redis_client()
        if not client:
            return None
        try:
            # Atomic RPOPLPUSH from queued to processing
            job_id = client.brpoplpush(cls.QUEUE_KEY, cls.PROCESSING_KEY, timeout=timeout)
            return job_id
        except Exception as e:
            logger.warning(f"Redis pop error: {e}")
            return None

    @classmethod
    def remove_processing_job(cls, job_id: str) -> None:
        client = get_redis_client()
        if not client:
            return
        try:
            client.lrem(cls.PROCESSING_KEY, 0, job_id)
        except Exception:
            pass

