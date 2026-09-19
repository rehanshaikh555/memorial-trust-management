"""add class permissions

Revision ID: fc1c9e3ae78e
Revises: 1a7f5e690717
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fc1c9e3ae78e"
down_revision: Union[str, Sequence[str], None] = "1a7f5e690717"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = {
    "class.create": "Class Create",
    "class.read": "Class Read",
    "class.update": "Class Update",
    "class.deactivate": "Class Deactivate",
}

ROLE_PERMISSIONS = {
    "SUPER_ADMIN": set(PERMISSIONS),
    "TRUST_ADMIN": set(PERMISSIONS),
    "SCHOOL_ADMIN": set(PERMISSIONS),
    "TEACHER": {"class.read"},
    "VIEWER": {"class.read"},
}


def upgrade() -> None:
    bind = op.get_bind()

    permission_ids = {}

    for name, description in PERMISSIONS.items():
        permission_id = bind.execute(
            sa.text(
                "SELECT id FROM permissions "
                "WHERE name = :name "
                "LIMIT 1"
            ),
            {"name": name},
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
                    "name": name,
                    "description": description,
                },
            ).scalar_one()

        permission_ids[name] = permission_id

    for role_name, permission_names in ROLE_PERMISSIONS.items():
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

        for permission_name in permission_names:
            exists = bind.execute(
                sa.text(
                    "SELECT 1 FROM role_permissions "
                    "WHERE role_id = :role_id "
                    "AND permission_id = :permission_id "
                    "LIMIT 1"
                ),
                {
                    "role_id": role_id,
                    "permission_id": permission_ids[permission_name],
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
                        "permission_id": permission_ids[permission_name],
                    },
                )


def downgrade() -> None:
    bind = op.get_bind()

    for name in PERMISSIONS:
        permission_id = bind.execute(
            sa.text(
                "SELECT id FROM permissions "
                "WHERE name = :name "
                "LIMIT 1"
            ),
            {"name": name},
        ).scalar_one_or_none()

        if permission_id is None:
            continue

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
