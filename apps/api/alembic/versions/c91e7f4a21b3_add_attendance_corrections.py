"""add attendance correction workflow

Revision ID: c91e7f4a21b3
Revises: 8b7c2d1e4f90
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c91e7f4a21b3"
down_revision: Union[str, None] = "8b7c2d1e4f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attendance_corrections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "attendance_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "attendance_date",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "old_status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "old_remarks",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "requested_status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "requested_remarks",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "review_remarks",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attendance_id"],
            ["attendance.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_attendance_corrections_attendance_id",
        "attendance_corrections",
        ["attendance_id"],
        unique=False,
    )

    op.create_index(
        "ix_attendance_corrections_school_id",
        "attendance_corrections",
        ["school_id"],
        unique=False,
    )

    op.create_index(
        "ix_attendance_corrections_attendance_date",
        "attendance_corrections",
        ["attendance_date"],
        unique=False,
    )

    op.create_index(
        "ix_attendance_corrections_status",
        "attendance_corrections",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_attendance_corrections_requested_by",
        "attendance_corrections",
        ["requested_by"],
        unique=False,
    )

    op.create_index(
        "ix_attendance_corrections_reviewed_by",
        "attendance_corrections",
        ["reviewed_by"],
        unique=False,
    )

    op.create_index(
        "ix_attendance_corrections_school_date",
        "attendance_corrections",
        ["school_id", "attendance_date"],
        unique=False,
    )

    op.create_index(
        "ix_attendance_corrections_status_requested",
        "attendance_corrections",
        ["status", "requested_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_attendance_corrections_status_requested",
        table_name="attendance_corrections",
    )
    op.drop_index(
        "ix_attendance_corrections_school_date",
        table_name="attendance_corrections",
    )
    op.drop_index(
        "ix_attendance_corrections_reviewed_by",
        table_name="attendance_corrections",
    )
    op.drop_index(
        "ix_attendance_corrections_requested_by",
        table_name="attendance_corrections",
    )
    op.drop_index(
        "ix_attendance_corrections_status",
        table_name="attendance_corrections",
    )
    op.drop_index(
        "ix_attendance_corrections_attendance_date",
        table_name="attendance_corrections",
    )
    op.drop_index(
        "ix_attendance_corrections_school_id",
        table_name="attendance_corrections",
    )
    op.drop_index(
        "ix_attendance_corrections_attendance_id",
        table_name="attendance_corrections",
    )
    op.drop_table("attendance_corrections")
