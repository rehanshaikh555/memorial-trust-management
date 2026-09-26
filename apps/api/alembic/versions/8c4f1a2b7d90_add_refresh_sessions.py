"""add refresh sessions

Revision ID: 8c4f1a2b7d90
Revises: 7edfba564016
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c4f1a2b7d90"
down_revision: str | Sequence[str] | None = "7edfba564016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "refresh_sessions",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "replaced_by_session_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_refresh_sessions_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_session_id"],
            ["refresh_sessions.id"],
            name="fk_refresh_sessions_replaced_by_session_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_refresh_sessions",
        ),
    )

    op.create_index(
        "ix_refresh_sessions_user_id",
        "refresh_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_refresh_sessions_token_hash",
        "refresh_sessions",
        ["token_hash"],
    )

    op.create_index(
        "ix_refresh_sessions_expires_at",
        "refresh_sessions",
        ["expires_at"],
        unique=False,
    )

    op.create_index(
        "ix_refresh_sessions_revoked_at",
        "refresh_sessions",
        ["revoked_at"],
        unique=False,
    )

    op.create_index(
        "ix_refresh_sessions_replaced_by_session_id",
        "refresh_sessions",
        ["replaced_by_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_refresh_sessions_replaced_by_session_id",
        table_name="refresh_sessions",
    )

    op.drop_index(
        "ix_refresh_sessions_revoked_at",
        table_name="refresh_sessions",
    )

    op.drop_index(
        "ix_refresh_sessions_expires_at",
        table_name="refresh_sessions",
    )

    op.drop_constraint(
        "uq_refresh_sessions_token_hash",
        "refresh_sessions",
        type_="unique",
    )

    op.drop_index(
        "ix_refresh_sessions_user_id",
        table_name="refresh_sessions",
    )

    op.drop_table("refresh_sessions")