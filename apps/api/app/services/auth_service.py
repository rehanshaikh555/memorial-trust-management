from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import AuthResponse, TokenResponse, UserResponse


class AuthenticationError(Exception):
    """Raised when authentication fails."""


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> AuthResponse:
    """Authenticate a user and issue access and refresh tokens."""

    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None:
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationError("User account is inactive.")

    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")

    role = db.scalar(
        select(Role).where(Role.id == user.role_id)
    )

    if role is None:
        raise AuthenticationError("User role is not configured.")

    role_name = role.name

    access_token = create_access_token(
        subject=str(user.id),
        role=role_name,
        extra_claims={
            "trust_id": str(user.trust_id) if user.trust_id else None,
        },
    )

    refresh_token = create_refresh_token(
        subject=str(user.id),
    )

    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            role=role_name,
            is_active=user.is_active,
            trust_id=str(user.trust_id) if user.trust_id else None,
        ),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
    )
