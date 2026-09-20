from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ATTENDANCE_STATUSES = {"PRESENT", "ABSENT", "LATE", "EXCUSED"}


class AttendanceEntry(BaseModel):
    enrollment_id: UUID
    status: Literal["PRESENT", "ABSENT", "LATE", "EXCUSED"]
    remarks: str | None = Field(default=None, max_length=500)


class BulkAttendanceRequest(BaseModel):
    school_id: UUID
    academic_year_id: UUID
    class_id: UUID
    attendance_date: date
    entries: list[AttendanceEntry] = Field(min_length=1)


class AttendanceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    enrollment_id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    class_id: UUID
    academic_year_id: UUID
    school_id: UUID
    attendance_date: date
    status: str
    remarks: str | None
    marked_by: UUID


class AttendanceSheetItem(BaseModel):
    enrollment_id: UUID
    student_id: UUID
    student_code: str
    student_name: str
    status: str | None
    remarks: str | None


class AttendanceSheetResponse(BaseModel):
    school_id: UUID
    academic_year_id: UUID
    class_id: UUID
    attendance_date: date
    is_working_day: bool
    items: list[AttendanceSheetItem]


class AttendanceBulkResponse(BaseModel):
    attendance_date: date
    count: int
    items: list[AttendanceItem]


class AttendanceCorrectionCreate(BaseModel):
    attendance_id: UUID
    requested_status: Literal["PRESENT", "ABSENT", "LATE", "EXCUSED"]
    requested_remarks: str | None = Field(default=None, max_length=500)
    reason: str = Field(min_length=3, max_length=2000)


class AttendanceCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    attendance_id: UUID
    school_id: UUID
    attendance_date: date
    old_status: str
    old_remarks: str | None
    requested_status: str
    requested_remarks: str | None
    reason: str
    status: str
    requested_by: UUID
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    review_remarks: str | None


class AttendanceCorrectionReview(BaseModel):
    remarks: str | None = Field(default=None, max_length=2000)


class CalendarCreate(BaseModel):
    school_id: UUID
    academic_year_id: UUID
    calendar_date: date
    is_working_day: bool = True
    day_type: str = Field(default="REGULAR", min_length=1, max_length=30)
    holiday_name: str | None = Field(default=None, max_length=255)
    remarks: str | None = Field(default=None, max_length=500)


class CalendarUpdate(BaseModel):
    is_working_day: bool | None = None
    day_type: str | None = Field(default=None, min_length=1, max_length=30)
    holiday_name: str | None = Field(default=None, max_length=255)
    remarks: str | None = Field(default=None, max_length=500)


class CalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    calendar_date: date
    is_working_day: bool
    day_type: str
    holiday_name: str | None
    remarks: str | None


class MonthlyAttendanceReport(BaseModel):
    student_id: UUID
    student_code: str
    student_name: str
    school_id: UUID
    academic_year_id: UUID
    month: int
    year: int
    working_days: int
    recorded_days: int
    present_days: int
    absent_days: int
    late_days: int
    excused_days: int
    attendance_percentage: float


class YearlyAttendanceReport(BaseModel):
    student_id: UUID
    student_code: str
    student_name: str
    school_id: UUID
    academic_year_id: UUID
    working_days: int
    recorded_days: int
    present_days: int
    absent_days: int
    late_days: int
    excused_days: int
    attendance_percentage: float
