from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission as PermissionModel
from app.models.role_permission import RolePermission
from app.models.user import User


def has_permission(db: Session, user: User, permission: str) -> bool:
    statement = (
        select(PermissionModel.id)
        .join(
            RolePermission,
            RolePermission.permission_id == PermissionModel.id,
        )
        .where(
            RolePermission.role_id == user.role_id,
            PermissionModel.name == permission,
        )
    )
    return db.scalar(statement) is not None


def require_permission(db: Session, user: User, permission: str) -> None:
    if not has_permission(db, user, permission):
        raise PermissionError(f"Permission denied: {permission}")
