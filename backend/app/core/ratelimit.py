from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_client_ip
from app.modules.database.repositories import BuildRepository, RateLimitRepository


def enforce_build_rate_limit(request: Request, db: Session) -> str:
    """
    Enforces build abuse protections:
    1. Global queue length limit.
    2. Max 1 active (queued or processing) build per IP.
    3. Hourly build quota per IP (sliding window).
    """
    client_ip = get_client_ip(request)

    # 1. Global queue capacity check
    queued_count = BuildRepository.count_queued_jobs(db)
    if queued_count >= settings.MAX_QUEUE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The build queue is currently full. Please try again in a few minutes.",
            headers={"Retry-After": "60"}
        )

    # 2. Max 1 active build per IP
    active_count = BuildRepository.count_active_jobs_for_ip(db, client_ip)
    if active_count >= 1:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You already have a build job queued or in progress. Please wait for it to complete.",
            headers={"Retry-After": "30"}
        )

    # 3. Sliding-window hourly quota per IP
    allowed, retry_after = RateLimitRepository.check_and_record(
        db=db,
        ip_address=client_ip,
        endpoint="POST /api/v1/builds",
        max_requests=settings.RATE_LIMIT_BUILDS_PER_HOUR,
        window_seconds=3600
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: Maximum {settings.RATE_LIMIT_BUILDS_PER_HOUR} builds per hour allowed per IP.",
            headers={"Retry-After": str(retry_after)}
        )

    return client_ip


def enforce_lightweight_rate_limit(request: Request, db: Session, endpoint: str = "general") -> str:
    """
    Lightweight rate limiting for status and download endpoints (e.g. 120 req/min).
    """
    client_ip = get_client_ip(request)
    allowed, retry_after = RateLimitRepository.check_and_record(
        db=db,
        ip_address=client_ip,
        endpoint=endpoint,
        max_requests=settings.RATE_LIMIT_STATUS_PER_MINUTE,
        window_seconds=60
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down.",
            headers={"Retry-After": str(retry_after)}
        )

    return client_ip
