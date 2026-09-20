"""fix attendance correction timestamps

Revision ID: 7edfba564016
Revises: c91e7f4a21b3
Create Date: 2026-09-19 23:34:45.686807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7edfba564016"
down_revision: Union[str, Sequence[str], None] = "c91e7f4a21b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add database defaults to attendance correction timestamps."""
    op.alter_column(
        "attendance_corrections",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "attendance_corrections",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=sa.text("now()"),
    )


def downgrade() -> None:
    """Remove database defaults from attendance correction timestamps."""
    op.alter_column(
        "attendance_corrections",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        "attendance_corrections",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=None,
    )
