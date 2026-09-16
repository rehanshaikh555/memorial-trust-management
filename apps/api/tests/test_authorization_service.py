from unittest.mock import Mock
from uuid import uuid4

from app.services.authorization_service import has_permission, require_permission


def make_db(permission_names: list[str]):
    db = Mock()

    def scalar(statement):
        params = statement.compile().params
        requested_permission = next(
            (value for value in params.values() if isinstance(value, str)),
            None,
        )

        if requested_permission in permission_names:
            return uuid4()

        return None

    db.scalar.side_effect = scalar
    return db


def make_user():
    user = Mock()
    user.id = uuid4()
    user.role_id = uuid4()
    return user


def test_role_permission_grants_requested_permission():
    user = make_user()
    db = make_db(["school.read"])

    assert has_permission(db, user, "school.read") is True


def test_role_permission_does_not_grant_different_permission():
    user = make_user()
    db = make_db(["school.read"])

    assert has_permission(db, user, "student.read") is False


def test_role_with_no_permissions_is_denied():
    user = make_user()
    db = make_db([])

    assert has_permission(db, user, "school.read") is False


def test_require_permission_allows_granted_permission():
    user = make_user()
    db = make_db(["student.read"])

    require_permission(db, user, "student.read")


def test_require_permission_rejects_missing_permission():
    user = make_user()
    db = make_db(["student.read"])

    try:
        require_permission(db, user, "school.read")
        assert False, "Expected PermissionError"
    except PermissionError:
        pass
