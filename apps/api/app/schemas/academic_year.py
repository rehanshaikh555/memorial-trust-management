from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AcademicYearCreate(BaseModel):
    trust_id: UUID
    name: str = Field(min_length=4, max_length=20)
    start_date: date
    end_date: date
    is_current: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class AcademicYearUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=4, max_length=20)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date >= self.end_date
        ):
            raise ValueError("start_date must be before end_date")
        return self


class AcademicYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trust_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
    is_active: bool


class SchoolAcademicYearCreate(BaseModel):
    school_id: UUID


class SchoolAcademicYearResponse(BaseModel):
    school_id: UUID
    academic_year_id: UUID
