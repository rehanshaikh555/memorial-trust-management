import uuid

from sqlalchemy import Boolean, ForeignKey, Index, PrimaryKeyConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentGuardian(Base):
    __tablename__ = "student_guardians"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    guardian_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guardians.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "student_id",
            "guardian_id",
        ),
        Index(
            "uq_student_guardians_one_primary",
            "student_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
    )
