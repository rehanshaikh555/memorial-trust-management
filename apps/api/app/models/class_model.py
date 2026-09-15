import uuid

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Class(TimestampMixin, Base):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    grade_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    section: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "uq_class_school_year_grade_section",
            "school_id",
            "academic_year_id",
            "grade_level",
            "section",
            unique=True,
            postgresql_where=section.is_not(None),
        ),
        Index(
            "uq_class_school_year_grade_no_section",
            "school_id",
            "academic_year_id",
            "grade_level",
            unique=True,
            postgresql_where=section.is_(None),
        ),
    )


