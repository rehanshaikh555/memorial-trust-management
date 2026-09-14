import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Attendance(TimestampMixin, Base):
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("enrollments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PRESENT",
        server_default=text("'PRESENT'"),
        index=True,
    )

    marked_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "uq_attendance_enrollment_date",
            "enrollment_id",
            "attendance_date",
            unique=True,
        ),
        Index(
            "ix_attendance_date_status",
            "attendance_date",
            "status",
        ),
    )
