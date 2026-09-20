from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationUnreadCount
from app.services.notification_service import (
    list_for_user,
    mark_all_read,
    mark_read,
    unread_count,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=list[NotificationResponse],
    dependencies=[
        Depends(require_permission(Permission.ACTIVITY_READ.value)),
    ],
)
def list_notifications(
    db: DbSession,
    current_user: CurrentUser,
    unread_only: bool = Query(default=False),
) -> list[NotificationResponse]:
    return list_for_user(
        db,
        user_id=current_user.id,
        unread_only=unread_only,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCount,
    dependencies=[
        Depends(require_permission(Permission.ACTIVITY_READ.value)),
    ],
)
def get_unread_count(
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationUnreadCount:
    return NotificationUnreadCount(
        unread_count=unread_count(
            db,
            user_id=current_user.id,
        )
    )


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    dependencies=[
        Depends(require_permission(Permission.ACTIVITY_READ.value)),
    ],
)
def mark_one_read(
    notification_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationResponse:
    notification = db.get(Notification, notification_id)

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    try:
        return mark_read(
            db,
            notification,
            user_id=current_user.id,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/read-all",
    response_model=NotificationUnreadCount,
    dependencies=[
        Depends(require_permission(Permission.ACTIVITY_READ.value)),
    ],
)
def mark_all_notifications_read(
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationUnreadCount:
    mark_all_read(
        db,
        user_id=current_user.id,
    )

    return NotificationUnreadCount(unread_count=0)
