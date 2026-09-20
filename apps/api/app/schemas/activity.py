from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActivityCreate(BaseModel):
    school_id: UUID
    academic_year_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    activity_date: date
    activity_type: str = Field(min_length=1, max_length=50)
    visibility: str = Field(default="INTERNAL", min_length=1, max_length=20)


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    activity_date: date | None = None
    activity_type: str | None = Field(default=None, min_length=1, max_length=50)
    visibility: str | None = Field(default=None, min_length=1, max_length=20)


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    title: str
    description: str | None
    activity_date: date
    activity_type: str
    status: str
    visibility: str
    created_by: UUID
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ActivityReject(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ActivityPhotoCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    storage_path: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=100)
    file_size: int = Field(gt=0)
    caption: str | None = Field(default=None, max_length=500)
    display_order: int = Field(default=0, ge=0)


class ActivityPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_id: UUID
    file_name: str
    storage_path: str
    mime_type: str
    file_size: int
    caption: str | None
    display_order: int
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime
