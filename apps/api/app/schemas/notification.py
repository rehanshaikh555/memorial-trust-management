from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_user_id: UUID
    notification_type: str
    title: str
    message: str
    related_entity_type: str | None
    related_entity_id: UUID | None
    priority: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationUnreadCount(BaseModel):
    unread_count: int
