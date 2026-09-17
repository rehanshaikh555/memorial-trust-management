from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.school import School
from app.models.user import User
from app.models.role import Role


TRUST_ID = uuid4()
OTHER_TRUST_ID = uuid4()
SCHOOL_A_ID = uuid4()
SCHOOL_B_ID = uuid4()
SCHOOL_C_ID = uuid4()
USER_ID = uuid4()
ROLE_ID = uuid4()


def make_user(*, trust_id=None):
    return User(
        id=USER_ID,
        trust_id=trust_id,
        role_id=ROLE_ID,
        email="admin@example.com",
        password_hash="unused",
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )


def make_role(name):
    return Role(
        id=ROLE_ID,
        name=name,
        description=f"{name} role",
    )


def make_school(
    *,
    school_id=SCHOOL_A_ID,
    trust_id=TRUST_ID,
    name="School A",
    code="SCHOOL-A",
):
    return School(
        id=school_id,
        trust_id=trust_id,
        name=name,
        code=code,
        address="Test Address",
        is_active=True,
    )


def setup_client(user):
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app), db


def teardown_client():
    app.dependency_overrides.clear()


def test_super_admin_can_list_all_schools():
    client, _ = setup_client(make_user())

    try:
        schools = [
            make_school(),
            make_school(
                school_id=SCHOOL_B_ID,
                trust_id=OTHER_TRUST_ID,
                name="School B",
                code="SCHOOL-B",
            ),
        ]

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.get_user_role",
            return_value=make_role("SUPER_ADMIN"),
        ), patch(
            "app.api.v1.school.SchoolService.list_all",
            return_value=schools,
        ) as list_mock:
            response = client.get("/api/v1/schools")

        assert response.status_code == 200
        assert len(response.json()) == 2

    finally:
        teardown_client()


def test_trust_admin_only_lists_own_trust_schools():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        schools = [
            make_school(),
        ]

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.get_user_role",
            return_value=make_role("TRUST_ADMIN"),
        ), patch(
            "app.api.v1.school.SchoolService.list_all",
            return_value=schools,
        ) as list_mock:
            response = client.get("/api/v1/schools")

        assert response.status_code == 200
        assert len(response.json()) == 1
        list_mock.assert_called_once_with(
            list_mock.call_args.args[0],
            trust_id=TRUST_ID,
        )

    finally:
        teardown_client()


def test_school_admin_only_lists_assigned_schools():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        schools = [
            make_school(),
        ]

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.get_user_role",
            return_value=make_role("SCHOOL_ADMIN"),
        ), patch(
            "app.api.v1.school.SchoolService.list_for_user",
            return_value=schools,
        ) as list_mock:
            response = client.get("/api/v1/schools")

        assert response.status_code == 200
        assert len(response.json()) == 1
        list_mock.assert_called_once_with(
            list_mock.call_args.args[0],
            USER_ID,
        )

    finally:
        teardown_client()


def test_teacher_only_lists_assigned_schools():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        schools = [
            make_school(),
        ]

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.get_user_role",
            return_value=make_role("TEACHER"),
        ), patch(
            "app.api.v1.school.SchoolService.list_for_user",
            return_value=schools,
        ) as list_mock:
            response = client.get("/api/v1/schools")

        assert response.status_code == 200
        assert len(response.json()) == 1
        list_mock.assert_called_once_with(
            list_mock.call_args.args[0],
            USER_ID,
        )

    finally:
        teardown_client()


def test_viewer_only_lists_assigned_schools():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        schools = [
            make_school(),
        ]

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.get_user_role",
            return_value=make_role("VIEWER"),
        ), patch(
            "app.api.v1.school.SchoolService.list_for_user",
            return_value=schools,
        ) as list_mock:
            response = client.get("/api/v1/schools")

        assert response.status_code == 200
        assert len(response.json()) == 1
        list_mock.assert_called_once_with(
            list_mock.call_args.args[0],
            USER_ID,
        )

    finally:
        teardown_client()


def test_unknown_role_returns_empty_school_list():
    client, _ = setup_client(make_user())

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.get_user_role",
            return_value=None,
        ):
            response = client.get("/api/v1/schools")

        assert response.status_code == 200
        assert response.json() == []

    finally:
        teardown_client()

def test_user_with_deactivate_permission_can_deactivate_school():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    school = make_school()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.SchoolService.get_by_id",
            return_value=school,
        ), patch(
            "app.api.v1.school.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.school.SchoolService.deactivate",
            return_value=school,
        ) as deactivate_mock:
            response = client.post(
                f"/api/v1/schools/{SCHOOL_A_ID}/deactivate"
            )

        assert response.status_code == 200
        assert response.json()["id"] == str(SCHOOL_A_ID)
        deactivate_mock.assert_called_once()

    finally:
        teardown_client()


def test_deactivate_school_returns_404_when_school_does_not_exist():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.SchoolService.get_by_id",
            return_value=None,
        ):
            response = client.post(
                f"/api/v1/schools/{SCHOOL_A_ID}/deactivate"
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "School not found."

    finally:
        teardown_client()


def test_deactivate_school_requires_deactivate_permission():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.post(
                f"/api/v1/schools/{SCHOOL_A_ID}/deactivate"
            )

        assert response.status_code == 403

    finally:
        teardown_client()


def test_deactivate_school_requires_school_access():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    school = make_school()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.SchoolService.get_by_id",
            return_value=school,
        ), patch(
            "app.api.v1.school.has_school_access",
            return_value=False,
        ):
            response = client.post(
                f"/api/v1/schools/{SCHOOL_A_ID}/deactivate"
            )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "You do not have access to this school."
        )

    finally:
        teardown_client()


def test_deactivate_school_returns_400_when_already_inactive():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    school = make_school()
    school.is_active = False

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.SchoolService.get_by_id",
            return_value=school,
        ), patch(
            "app.api.v1.school.has_school_access",
            return_value=True,
        ):
            response = client.post(
                f"/api/v1/schools/{SCHOOL_A_ID}/deactivate"
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "School is already inactive."

    finally:
        teardown_client()


def test_deactivate_school_returns_409_when_service_fails():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    school = make_school()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.school.SchoolService.get_by_id",
            return_value=school,
        ), patch(
            "app.api.v1.school.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.school.SchoolService.deactivate",
            side_effect=ValueError("Unable to deactivate school."),
        ):
            response = client.post(
                f"/api/v1/schools/{SCHOOL_A_ID}/deactivate"
            )

        assert response.status_code == 409
        assert response.json()["detail"] == "Unable to deactivate school."

    finally:
        teardown_client()
