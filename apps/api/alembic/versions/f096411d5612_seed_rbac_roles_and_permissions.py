"""seed rbac roles and permissions

Revision ID: f096411d5612
Revises: 58325af466da
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f096411d5612"
down_revision: Union[str, Sequence[str], None] = "58325af466da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = [
    "trust.create",
    "trust.read",
    "trust.update",
    "school.create",
    "school.read",
    "school.update",
    "school.deactivate",
    "student.create",
    "student.read",
    "student.update",
    "student.approve",
    "student.transfer",
    "student.exit",
    "document.read",
    "document.upload",
    "document.verify",
    "document.reject",
    "teacher.create",
    "teacher.read",
    "teacher.update",
    "teacher.assign",
    "attendance.create",
    "attendance.read",
    "attendance.correct",
    "activity.read",
    "activity.update",
    "activity.submit",
    "activity.approve",
    "activity.publish",
    "report.read",
    "report.generate",
    "audit.read",
    "academic_year.create",
    "academic_year.read",
    "academic_year.update",
    "academic_year.set_current",
    "academic_year.deactivate",
]


ROLES = {
    "SUPER_ADMIN": set(PERMISSIONS),
    "TRUST_ADMIN": set(PERMISSIONS),

    "SCHOOL_ADMIN": {
        "school.read",
        "school.update",
        "student.create",
        "student.read",
        "student.update",
        "student.approve",
        "student.transfer",
        "student.exit",
        "document.read",
        "document.upload",
        "document.verify",
        "document.reject",
        "teacher.create",
        "teacher.read",
        "teacher.update",
        "teacher.assign",
        "attendance.create",
        "attendance.read",
        "attendance.correct",
        "activity.read",
        "activity.update",
        "activity.submit",
        "report.read",
        "report.generate",
        "academic_year.read",
    },

    "TEACHER": {
        "student.read",
        "document.read",
        "teacher.read",
        "attendance.create",
        "attendance.read",
        "activity.read",
        "activity.update",
        "activity.submit",
        "report.read",
        "academic_year.read",
    },

    "VIEWER": {
        "trust.read",
        "school.read",
        "student.read",
        "document.read",
        "teacher.read",
        "attendance.read",
        "activity.read",
        "report.read",
        "audit.read",
        "academic_year.read",
    },
}


def upgrade() -> None:
    """Seed initial roles, permissions, and mappings."""
    bind = op.get_bind()

    permission_ids = {}
    role_ids = {}

    for name in PERMISSIONS:
        permission_id = bind.execute(
            sa.text(
                "SELECT id FROM permissions "
                "WHERE name = :name "
                "ORDER BY id "
                "LIMIT 1"
            ),
            {"name": name},
        ).scalar_one_or_none()

        if permission_id is None:
            permission_id = bind.execute(
                sa.text(
                    "INSERT INTO permissions "
                    "(id, name, description, created_at, updated_at) "
                    "VALUES (gen_random_uuid(), :name, :description, NOW(), NOW()) "
                    "RETURNING id"
                ),
                {
                    "name": name,
                    "description": name.replace(".", " ").title(),
                },
            ).scalar_one()

        permission_ids[name] = permission_id

    for name in ROLES:
        role_id = bind.execute(
            sa.text(
                "SELECT id FROM roles "
                "WHERE name = :name "
                "LIMIT 1"
            ),
            {"name": name},
        ).scalar_one_or_none()

        if role_id is None:
            role_id = bind.execute(
                sa.text(
                    "INSERT INTO roles "
                    "(id, name, description, created_at, updated_at) "
                    "VALUES (gen_random_uuid(), :name, :description, NOW(), NOW()) "
                    "RETURNING id"
                ),
                {
                    "name": name,
                    "description": name.replace("_", " ").title(),
                },
            ).scalar_one()

        role_ids[name] = role_id

    for role_name, role_permissions in ROLES.items():
        for permission_name in role_permissions:
            bind.execute(
                sa.text(
                    "INSERT INTO role_permissions "
                    "(role_id, permission_id) "
                    "SELECT :role_id, :permission_id "
                    "WHERE NOT EXISTS ("
                    "SELECT 1 FROM role_permissions "
                    "WHERE role_id = :role_id "
                    "AND permission_id = :permission_id"
                    ")"
                ),
                {
                    "role_id": role_ids[role_name],
                    "permission_id": permission_ids[permission_name],
                },
            )


def downgrade() -> None:
    """Remove the seeded RBAC records."""
    bind = op.get_bind()

    role_names = [
        "SUPER_ADMIN",
        "TRUST_ADMIN",
        "SCHOOL_ADMIN",
        "TEACHER",
        "VIEWER",
    ]

    bind.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE role_id IN ("
            "SELECT id FROM roles "
            "WHERE name IN (:r1, :r2, :r3, :r4, :r5)"
            ")"
        ),
        {
            "r1": role_names[0],
            "r2": role_names[1],
            "r3": role_names[2],
            "r4": role_names[3],
            "r5": role_names[4],
        },
    )

    bind.execute(
        sa.text(
            "DELETE FROM roles "
            "WHERE name IN (:r1, :r2, :r3, :r4, :r5)"
        ),
        {
            "r1": role_names[0],
            "r2": role_names[1],
            "r3": role_names[2],
            "r4": role_names[3],
            "r5": role_names[4],
        },
    )

    bind.execute(
        sa.text(
            "DELETE FROM permissions "
            "WHERE name IN ("
            "'academic_year.create',"
            "'academic_year.read',"
            "'academic_year.update',"
            "'academic_year.set_current',"
            "'academic_year.deactivate'"
            ")"
        )
    )
