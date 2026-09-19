from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClassCreate(BaseModel):
    school_id: UUID
    academic_year_id: UUID
    name: str = Field(min_length=1, max_length=100)
    grade_level: int = Field(ge=1, le=12)
    section: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def normalize_section(self):
        if self.section is not None:
            self.section = self.section.strip() or None
        return self


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    grade_level: int | None = Field(default=None, ge=1, le=12)
    section: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def normalize_section(self):
        if self.section is not None:
            self.section = self.section.strip() or None
        return self


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    name: str
    grade_level: int
    section: str | None
    is_active: bool
