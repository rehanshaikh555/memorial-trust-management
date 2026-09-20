from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification


def create(
    db: Session,
    *,
    recipient_user_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    related_entity_type: str | None = None,
    related_entity_id: UUID | None = None,
    priority: str = "NORMAL",
) -> Notification:
    notification = Notification(
        recipient_user_id=recipient_user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        priority=priority,
        is_read=False,
    )
    db.add(notification)
    db.flush()
    return notification


def create_many(
    db: Session,
    *,
    recipient_user_ids: list[UUID],
    notification_type: str,
    title: str,
    message: str,
    related_entity_type: str | None = None,
    related_entity_id: UUID | None = None,
    priority: str = "NORMAL",
) -> list[Notification]:
    result = []

    for recipient_id in dict.fromkeys(recipient_user_ids):
        result.append(
            create(
                db,
                recipient_user_id=recipient_id,
                notification_type=notification_type,
                title=title,
                message=message,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                priority=priority,
            )
        )

    return result


def list_for_user(
    db: Session,
    *,
    user_id: UUID,
    unread_only: bool = False,
) -> list[Notification]:
    statement = select(Notification).where(
        Notification.recipient_user_id == user_id
    )

    if unread_only:
        statement = statement.where(Notification.is_read.is_(False))

    statement = statement.order_by(Notification.created_at.desc())

    return list(db.scalars(statement).all())


def unread_count(
    db: Session,
    *,
    user_id: UUID,
) -> int:
    statement = select(func.count(Notification.id)).where(
        Notification.recipient_user_id == user_id,
        Notification.is_read.is_(False),
    )
    return int(db.scalar(statement) or 0)


def mark_read(
    db: Session,
    notification: Notification,
    *,
    user_id: UUID,
) -> Notification:
    if notification.recipient_user_id != user_id:
        raise PermissionError("You cannot modify this notification.")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(
    db: Session,
    *,
    user_id: UUID,
) -> int:
    notifications = list(
        db.scalars(
            select(Notification).where(
                Notification.recipient_user_id == user_id,
                Notification.is_read.is_(False),
            )
        ).all()
    )

    now = datetime.now(timezone.utc)

    for notification in notifications:
        notification.is_read = True
        notification.read_at = now

    db.commit()

    return len(notifications)
