import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class AttendanceCorrection(TimestampMixin, Base):
    __tablename__ = "attendance_corrections"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    attendance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("attendance.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    old_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    old_remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    requested_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    requested_remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )

    requested_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    review_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_attendance_corrections_school_date",
            "school_id",
            "attendance_date",
        ),
        Index(
            "ix_attendance_corrections_status_requested",
            "status",
            "requested_by",
        ),
    )
