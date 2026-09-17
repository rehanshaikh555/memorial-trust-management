from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchoolCreate(BaseModel):
    trust_id: UUID
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=2, max_length=50)
    address: str | None = Field(default=None, max_length=500)


class SchoolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    address: str | None = Field(default=None, max_length=500)


class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trust_id: UUID
    name: str
    code: str
    address: str | None
    is_active: bool
