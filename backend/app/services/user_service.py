from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserResponse


def ensure_system_user(db: Session) -> User:
    settings = get_settings()
    user = db.get(User, settings.system_user_id)
    if user is not None:
        return user

    user = User(
        id=settings.system_user_id,
        username=settings.system_username,
        password_hash="",
        status="active",
        created_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_user(db: Session, payload: UserCreate) -> UserResponse:
    username = payload.username.strip()
    if not username:
        raise ValueError("Username is required")
    existing = db.scalar(select(User).where(User.username == username))
    if existing is not None:
        raise ValueError("Username already exists")

    user = User(
        id=f"user-{uuid4().hex[:12]}",
        username=username,
        password_hash=hash_password(payload.password),
        status="active",
        created_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return to_user_response(user)


def authenticate_user(db: Session, username: str, password: str) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == username.strip()))
    if user is None or user.status != "active":
        raise ValueError("Invalid username or password")
    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid username or password")

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=to_user_response(user),
    )


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        status=user.status,
        created_at=user.created_at.isoformat(),
    )
