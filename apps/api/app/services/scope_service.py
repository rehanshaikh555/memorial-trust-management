from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.school import School
from app.models.user import User
from app.models.user_school_access import UserSchoolAccess


SUPER_ADMIN = "SUPER_ADMIN"
TRUST_ADMIN = "TRUST_ADMIN"
SCHOOL_ADMIN = "SCHOOL_ADMIN"
TEACHER = "TEACHER"
VIEWER = "VIEWER"


def get_user_role(db: Session, user: User) -> Role | None:
    return db.scalar(select(Role).where(Role.id == user.role_id))


def has_school_access(db: Session, user: User, school_id: UUID) -> bool:
    role = get_user_role(db, user)

    if role is None:
        return False

    if role.name == SUPER_ADMIN:
        return True

    school = db.scalar(select(School).where(School.id == school_id))

    if school is None or not school.is_active:
        return False

    if role.name == TRUST_ADMIN:
        return user.trust_id is not None and school.trust_id == user.trust_id

    if role.name in {SCHOOL_ADMIN, TEACHER, VIEWER}:
        access = db.scalar(
            select(UserSchoolAccess).where(
                UserSchoolAccess.user_id == user.id,
                UserSchoolAccess.school_id == school_id,
            )
        )
        return access is not None

    return False


def has_trust_access(db: Session, user: User, trust_id: UUID) -> bool:
    role = get_user_role(db, user)
    if role is None:
        return False

    if role.name == SUPER_ADMIN:
        return True

    return user.trust_id is not None and user.trust_id == trust_id
