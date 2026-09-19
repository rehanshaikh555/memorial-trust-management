from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GuardianCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    relationship: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = Field(default=None, max_length=500)
    is_primary: bool = False

    @model_validator(mode="after")
    def normalize(self):
        self.full_name = self.full_name.strip()
        self.relationship = self.relationship.strip()
        self.phone = self.phone.strip()
        if self.email is not None:
            self.email = self.email.strip() or None
        if self.address is not None:
            self.address = self.address.strip() or None
        return self


class GuardianUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    relationship: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = Field(default=None, max_length=500)
    is_primary: bool | None = None

    @model_validator(mode="after")
    def normalize(self):
        for field in ("full_name", "relationship", "phone"):
            value = getattr(self, field)
            if value is not None:
                setattr(self, field, value.strip())
        if self.email is not None:
            self.email = self.email.strip() or None
        if self.address is not None:
            self.address = self.address.strip() or None
        return self


class StudentCreate(BaseModel):
    student_id: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = None

    school_id: UUID
    academic_year_id: UUID
    class_id: UUID
    enrollment_date: date
    guardians: list[GuardianCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize(self):
        self.student_id = self.student_id.strip()
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()

        if self.middle_name is not None:
            self.middle_name = self.middle_name.strip() or None
        if self.gender is not None:
            self.gender = self.gender.strip() or None
        if self.phone is not None:
            self.phone = self.phone.strip() or None
        if self.email is not None:
            self.email = self.email.strip() or None
        if self.address is not None:
            self.address = self.address.strip() or None

        if self.enrollment_date < self.date_of_birth:
            raise ValueError("enrollment_date cannot be before date_of_birth.")

        return self


class StudentUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = None

    @model_validator(mode="after")
    def normalize(self):
        for field in ("first_name", "last_name", "gender", "phone", "email", "address"):
            value = getattr(self, field)
            if value is not None:
                setattr(self, field, value.strip() or None)

        if self.middle_name is not None:
            self.middle_name = self.middle_name.strip() or None

        return self


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: str
    first_name: str
    middle_name: str | None
    last_name: str
    date_of_birth: date
    gender: str | None
    phone: str | None
    email: str | None
    address: str | None
    status: str
    is_active: bool


class GuardianResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    relationship: str
    phone: str
    email: str | None
    address: str | None
    is_primary: bool


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    school_id: UUID
    academic_year_id: UUID
    class_id: UUID
    enrollment_date: date
    exit_date: date | None
    status: str


class StudentDetailResponse(StudentResponse):
    guardians: list[GuardianResponse]
    enrollment: EnrollmentResponse | None


class StudentListResponse(StudentResponse):
    school_id: UUID | None = None
    academic_year_id: UUID | None = None
    class_id: UUID | None = None


class StudentTransfer(BaseModel):
    school_id: UUID
    academic_year_id: UUID
    class_id: UUID
    enrollment_date: date


class StudentDocumentCreate(BaseModel):
    document_type: str = Field(min_length=1, max_length=50)
    file_name: str = Field(min_length=1, max_length=255)
    storage_path: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=100)
    file_size: int = Field(gt=0)
    expiry_date: date | None = None

    @model_validator(mode="after")
    def normalize(self):
        self.document_type = self.document_type.strip().upper()
        self.file_name = self.file_name.strip()
        self.storage_path = self.storage_path.strip()
        self.mime_type = self.mime_type.strip().lower()
        return self


class StudentDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    document_type: str
    file_name: str
    storage_path: str
    mime_type: str
    file_size: int
    status: str
    rejection_reason: str | None
    expiry_date: date | None


class DocumentDecision(BaseModel):
    remarks: str | None = Field(default=None, max_length=1000)


class DocumentRejection(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)