"""add missing activity create permission

Revision ID: 2ca85bacfb2e
Revises: f096411d5612
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2ca85bacfb2e"
down_revision: Union[str, Sequence[str], None] = "f096411d5612"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    permission_id = bind.execute(
        sa.text(
            "SELECT id FROM permissions "
            "WHERE name = :name "
            "LIMIT 1"
        ),
        {"name": "activity.create"},
    ).scalar_one_or_none()

    if permission_id is None:
        permission_id = bind.execute(
            sa.text(
                "INSERT INTO permissions "
                "(id, name, description, created_at, updated_at) "
                "VALUES "
                "(gen_random_uuid(), :name, :description, NOW(), NOW()) "
                "RETURNING id"
            ),
            {
                "name": "activity.create",
                "description": "Activity Create",
            },
        ).scalar_one()

    role_names = [
        "SUPER_ADMIN",
        "TRUST_ADMIN",
        "SCHOOL_ADMIN",
        "TEACHER",
    ]

    for role_name in role_names:
        role_id = bind.execute(
            sa.text(
                "SELECT id FROM roles "
                "WHERE name = :name "
                "LIMIT 1"
            ),
            {"name": role_name},
        ).scalar_one_or_none()

        if role_id is None:
            raise RuntimeError(
                f"Required RBAC role not found: {role_name}"
            )

        exists = bind.execute(
            sa.text(
                "SELECT 1 FROM role_permissions "
                "WHERE role_id = :role_id "
                "AND permission_id = :permission_id "
                "LIMIT 1"
            ),
            {
                "role_id": role_id,
                "permission_id": permission_id,
            },
        ).scalar_one_or_none()

        if exists is None:
            bind.execute(
                sa.text(
                    "INSERT INTO role_permissions "
                    "(role_id, permission_id) "
                    "VALUES (:role_id, :permission_id)"
                ),
                {
                    "role_id": role_id,
                    "permission_id": permission_id,
                },
            )


def downgrade() -> None:
    bind = op.get_bind()

    permission_id = bind.execute(
        sa.text(
            "SELECT id FROM permissions "
            "WHERE name = :name "
            "LIMIT 1"
        ),
        {"name": "activity.create"},
    ).scalar_one_or_none()

    if permission_id is None:
        return

    bind.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id = :permission_id"
        ),
        {"permission_id": permission_id},
    )

    bind.execute(
        sa.text(
            "DELETE FROM permissions "
            "WHERE id = :permission_id"
        ),
        {"permission_id": permission_id},
    )
