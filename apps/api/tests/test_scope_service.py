from unittest.mock import Mock
from uuid import uuid4

from app.services.scope_service import (
    SUPER_ADMIN,
    TRUST_ADMIN,
    SCHOOL_ADMIN,
    TEACHER,
    VIEWER,
    has_school_access,
    has_trust_access,
)


def make_db(role_name: str | None, *, trust_id=None, school=None, access=False):
    db = Mock()

    role = None if role_name is None else Mock(name="Role")
    if role is not None:
        role.name = role_name

    def scalar(statement):
        text = str(statement)
        if "FROM roles" in text:
            return role
        if "FROM schools" in text:
            return school
        if "FROM user_school_access" in text:
            return Mock() if access else None
        return None

    db.scalar.side_effect = scalar
    return db


def make_user(trust_id=None):
    user = Mock()
    user.id = uuid4()
    user.role_id = uuid4()
    user.trust_id = trust_id
    return user


def make_school(trust_id, active=True):
    school = Mock()
    school.id = uuid4()
    school.trust_id = trust_id
    school.is_active = active
    return school


def test_super_admin_has_school_access():
    school_id = uuid4()
    user = make_user()
    db = make_db(SUPER_ADMIN)

    assert has_school_access(db, user, school_id) is True


def test_trust_admin_can_access_school_in_own_trust():
    trust_id = uuid4()
    school = make_school(trust_id)
    user = make_user(trust_id)
    db = make_db(TRUST_ADMIN, school=school)

    assert has_school_access(db, user, school.id) is True


def test_trust_admin_cannot_access_school_in_another_trust():
    user_trust = uuid4()
    other_trust = uuid4()
    school = make_school(other_trust)
    user = make_user(user_trust)
    db = make_db(TRUST_ADMIN, school=school)

    assert has_school_access(db, user, school.id) is False


def test_school_admin_requires_explicit_school_access():
    school = make_school(uuid4())
    user = make_user(uuid4())

    db = make_db(SCHOOL_ADMIN, school=school, access=False)
    assert has_school_access(db, user, school.id) is False

    db = make_db(SCHOOL_ADMIN, school=school, access=True)
    assert has_school_access(db, user, school.id) is True


def test_teacher_requires_explicit_school_access():
    school = make_school(uuid4())
    user = make_user(uuid4())

    db = make_db(TEACHER, school=school, access=False)
    assert has_school_access(db, user, school.id) is False


def test_viewer_requires_explicit_school_access():
    school = make_school(uuid4())
    user = make_user(uuid4())

    db = make_db(VIEWER, school=school, access=True)
    assert has_school_access(db, user, school.id) is True


def test_inactive_school_is_denied():
    school = make_school(uuid4(), active=False)
    user = make_user(school.trust_id)
    db = make_db(TRUST_ADMIN, school=school)

    assert has_school_access(db, user, school.id) is False


def test_missing_role_is_denied():
    user = make_user()
    db = make_db(None)

    assert has_school_access(db, user, uuid4()) is False
    assert has_trust_access(db, user, uuid4()) is False


def test_super_admin_has_trust_access():
    user = make_user()
    db = make_db(SUPER_ADMIN)

    assert has_trust_access(db, user, uuid4()) is True


def test_user_has_trust_access_only_for_own_trust():
    trust_id = uuid4()
    user = make_user(trust_id)
    db = make_db(TRUST_ADMIN, trust_id=trust_id)

    assert has_trust_access(db, user, trust_id) is True
    assert has_trust_access(db, user, uuid4()) is False
