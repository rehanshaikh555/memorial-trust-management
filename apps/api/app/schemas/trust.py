from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrustCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=2000)


class TrustUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None


class TrustResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    description: str | None
    is_active: bool
