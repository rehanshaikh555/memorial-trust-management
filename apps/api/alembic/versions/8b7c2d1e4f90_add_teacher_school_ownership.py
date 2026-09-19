"""add school ownership to teachers

Revision ID: 8b7c2d1e4f90
Revises: fc1c9e3ae78e
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "8b7c2d1e4f90"
down_revision = "fc1c9e3ae78e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "teachers",
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_teachers_school_id",
        "teachers",
        ["school_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_teachers_school_id",
        "teachers",
        "schools",
        ["school_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.execute(
        """
        UPDATE teachers AS t
        SET school_id = (
            SELECT ta.school_id
            FROM teacher_assignments AS ta
            WHERE ta.teacher_id = t.id
            ORDER BY
                CASE WHEN ta.status = 'ACTIVE' THEN 0 ELSE 1 END,
                ta.start_date DESC,
                ta.id
            LIMIT 1
        )
        """
    )

    remaining = op.get_bind().execute(
        sa.text(
            "SELECT COUNT(*) FROM teachers WHERE school_id IS NULL"
        )
    ).scalar_one()

    if remaining:
        raise RuntimeError(
            f"Cannot make teachers.school_id NOT NULL; "
            f"{remaining} teacher record(s) have no school ownership."
        )

    op.alter_column(
        "teachers",
        "school_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )


def downgrade():
    op.drop_constraint(
        "fk_teachers_school_id",
        "teachers",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_teachers_school_id",
        table_name="teachers",
    )
    op.drop_column("teachers", "school_id")
