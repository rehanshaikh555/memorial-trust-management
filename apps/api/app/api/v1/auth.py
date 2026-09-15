from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthenticationError, authenticate_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    """Authenticate a user and issue access and refresh tokens."""

    try:
        return authenticate_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_token(
    payload: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Exchange a valid refresh token for a new access/refresh pair."""

    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = token_payload.get("sub")

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(
        select(User).where(User.id == subject)
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = db.scalar(
        select(Role).where(Role.id == user.role_id)
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is not configured.",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=role.name,
        extra_claims={
            "trust_id": str(user.trust_id) if user.trust_id else None,
        },
    )

    new_refresh_token = create_refresh_token(
        subject=str(user.id),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Return the currently authenticated user."""

    role = db.scalar(
        select(Role).where(Role.id == current_user.role_id)
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role is not configured.",
        )

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=role.name,
        is_active=current_user.is_active,
        trust_id=(
            str(current_user.trust_id)
            if current_user.trust_id
            else None
        ),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    current_user: CurrentUser,
) -> None:
    """End the client authentication session.

    JWTs are currently stateless. Actual token revocation will be added
    when server-side refresh-token/session storage is introduced.
    """

    return None
