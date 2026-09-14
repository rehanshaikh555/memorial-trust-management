import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class SchoolCalendar(TimestampMixin, Base):
    __tablename__ = "school_calendar"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    calendar_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    is_working_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    day_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="REGULAR",
        server_default=text("'REGULAR'"),
    )

    holiday_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "uq_school_calendar_school_year_date",
            "school_id",
            "academic_year_id",
            "calendar_date",
            unique=True,
        ),
    )
