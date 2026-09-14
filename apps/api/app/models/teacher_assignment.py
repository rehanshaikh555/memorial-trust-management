import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class TeacherAssignment(TimestampMixin, Base):
    __tablename__ = "teacher_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    class_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    subject: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_teacher_assignments_school_year",
            "school_id",
            "academic_year_id",
        ),
        Index(
            "ix_teacher_assignments_teacher_year",
            "teacher_id",
            "academic_year_id",
        ),
    )
