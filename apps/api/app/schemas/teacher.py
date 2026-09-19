from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TeacherCreate(BaseModel):
    school_id: UUID
    teacher_id: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = Field(default=None, max_length=500)
    qualification: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def normalize(self):
        self.teacher_id = self.teacher_id.strip()
        self.first_name = self.first_name.strip()
        if self.middle_name is not None:
            self.middle_name = self.middle_name.strip() or None
        if self.last_name is not None:
            self.last_name = self.last_name.strip() or None
        return self


class TeacherUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = Field(default=None, max_length=500)
    qualification: str | None = Field(default=None, max_length=255)


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    teacher_id: str
    first_name: str
    middle_name: str | None
    last_name: str | None
    date_of_birth: date | None
    gender: str | None
    phone: str | None
    email: str | None
    address: str | None
    qualification: str | None
    status: str
    is_active: bool


class TeacherAssignmentCreate(BaseModel):
    teacher_id: UUID
    school_id: UUID
    academic_year_id: UUID
    class_id: UUID | None = None
    subject: str | None = Field(default=None, max_length=100)
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date.")
        return self


class TeacherAssignmentUpdate(BaseModel):
    class_id: UUID | None = None
    subject: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, max_length=30)


class TeacherAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID
    school_id: UUID
    academic_year_id: UUID
    class_id: UUID | None
    subject: str | None
    start_date: date
    end_date: date | None
    status: str


class TeacherAttendanceCreate(BaseModel):
    teacher_id: UUID
    attendance_date: date
    status: str = Field(default="PRESENT", min_length=1, max_length=20)
    remarks: str | None = Field(default=None, max_length=500)


class TeacherAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID
    attendance_date: date
    status: str
    marked_by: UUID
    remarks: str | None