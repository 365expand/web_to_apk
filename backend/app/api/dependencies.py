from typing import Any, Dict, Optional
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.security import get_client_ip
from app.modules.database.engine import get_db


class User:
    def __init__(self, user_id: Optional[str] = None, role: str = "anonymous"):
        self.user_id = user_id
        self.role = role

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None


def get_current_user(request: Request) -> User:
    """
    Authentication dependency hook.
    Returns an anonymous user today. Real authentication (JWT, OAuth, etc.)
    will plug in here in future versions without changing route signatures.
    """
    # Header hook for future auth token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Placeholder for future token decoding
        token = auth_header[7:].strip()
        if token:
            return User(user_id=f"user_{token[:8]}", role="user")

    return User(user_id=None, role="anonymous")
