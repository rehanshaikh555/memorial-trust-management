from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.academic_year import AcademicYear
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear
from app.models.user import User
from app.models.role import Role


TRUST_ID = uuid4()
OTHER_TRUST_ID = uuid4()
ACADEMIC_YEAR_ID = uuid4()
ACADEMIC_YEAR_B_ID = uuid4()
SCHOOL_ID = uuid4()
OTHER_SCHOOL_ID = uuid4()
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


def make_role(name="TRUST_ADMIN"):
    return Role(
        id=ROLE_ID,
        name=name,
        description=f"{name} role",
    )


def make_academic_year(
    *,
    academic_year_id=ACADEMIC_YEAR_ID,
    trust_id=TRUST_ID,
    name="2026-2027",
    is_current=False,
    is_active=True,
):
    return AcademicYear(
        id=academic_year_id,
        trust_id=trust_id,
        name=name,
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=is_current,
        is_active=is_active,
    )


def make_school(
    *,
    school_id=SCHOOL_ID,
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

def test_create_academic_year():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.create",
            return_value=academic_year,
        ) as create_mock:
            response = client.post(
                "/api/v1/academic-years",
                json={
                    "trust_id": str(TRUST_ID),
                    "name": "2026-2027",
                    "start_date": "2026-04-01",
                    "end_date": "2027-03-31",
                    "is_current": False,
                },
            )

        assert response.status_code == 201
        assert response.json()["id"] == str(ACADEMIC_YEAR_ID)
        assert response.json()["name"] == "2026-2027"
        create_mock.assert_called_once()

    finally:
        teardown_client()


def test_create_academic_year_requires_trust_access():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/academic-years",
                json={
                    "trust_id": str(OTHER_TRUST_ID),
                    "name": "2026-2027",
                    "start_date": "2026-04-01",
                    "end_date": "2027-03-31",
                },
            )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "You do not have access to this trust."
        )

    finally:
        teardown_client()


def test_create_academic_year_duplicate_returns_409():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.create",
            side_effect=ValueError(
                "An academic year with this name already exists."
            ),
        ):
            response = client.post(
                "/api/v1/academic-years",
                json={
                    "trust_id": str(TRUST_ID),
                    "name": "2026-2027",
                    "start_date": "2026-04-01",
                    "end_date": "2027-03-31",
                },
            )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    finally:
        teardown_client()


def test_create_academic_year_invalid_dates_returns_422():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ):
            response = client.post(
                "/api/v1/academic-years",
                json={
                    "trust_id": str(TRUST_ID),
                    "name": "2026-2027",
                    "start_date": "2027-04-01",
                    "end_date": "2026-03-31",
                },
            )

        assert response.status_code == 422

    finally:
        teardown_client()


def test_list_academic_years():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_years = [
        make_academic_year(),
        make_academic_year(
            academic_year_id=ACADEMIC_YEAR_B_ID,
            name="2027-2028",
        ),
    ]

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.list_all",
            return_value=academic_years,
        ) as list_mock:
            response = client.get(
                f"/api/v1/academic-years?trust_id={TRUST_ID}"
            )

        assert response.status_code == 200
        assert len(response.json()) == 2
        list_mock.assert_called_once_with(
            list_mock.call_args.args[0],
            trust_id=TRUST_ID,
        )

    finally:
        teardown_client()


def test_get_academic_year():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ):
            response = client.get(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}"
            )

        assert response.status_code == 200
        assert response.json()["id"] == str(ACADEMIC_YEAR_ID)

    finally:
        teardown_client()


def test_get_academic_year_returns_404_when_missing():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=None,
        ):
            response = client.get(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}"
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Academic year not found."

    finally:
        teardown_client()


def test_get_academic_year_requires_trust_access():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=False,
        ):
            response = client.get(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}"
            )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "You do not have access to this trust."
        )

    finally:
        teardown_client()

def test_update_academic_year():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()
    updated = make_academic_year(name="2026-2028")

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.update",
            return_value=updated,
        ) as update_mock:
            response = client.patch(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}",
                json={"name": "2026-2028"},
            )

        assert response.status_code == 200
        assert response.json()["name"] == "2026-2028"
        update_mock.assert_called_once()

    finally:
        teardown_client()


def test_update_academic_year_returns_409_on_duplicate():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.update",
            side_effect=ValueError(
                "An academic year with this name already exists."
            ),
        ):
            response = client.patch(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}",
                json={"name": "2025-2026"},
            )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    finally:
        teardown_client()


def test_update_academic_year_requires_trust_access():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=False,
        ):
            response = client.patch(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}",
                json={"name": "Updated Year"},
            )

        assert response.status_code == 403

    finally:
        teardown_client()


def test_set_current_academic_year():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()
    academic_year.is_current = True

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=make_academic_year(),
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.set_current",
            return_value=academic_year,
        ) as set_current_mock:
            response = client.post(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/set-current"
            )

        assert response.status_code == 200
        assert response.json()["is_current"] is True
        set_current_mock.assert_called_once()

    finally:
        teardown_client()


def test_set_current_inactive_academic_year_returns_400():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year(is_active=False)

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.set_current",
            side_effect=ValueError(
                "Inactive academic year cannot be set as current."
            ),
        ):
            response = client.post(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/set-current"
            )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Inactive academic year cannot be set as current."
        )

    finally:
        teardown_client()


def test_set_current_requires_trust_access():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=False,
        ):
            response = client.post(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/set-current"
            )

        assert response.status_code == 403

    finally:
        teardown_client()


def test_deactivate_academic_year():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()
    deactivated = make_academic_year(is_active=False)

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.deactivate",
            return_value=deactivated,
        ) as deactivate_mock:
            response = client.post(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/deactivate"
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False
        deactivate_mock.assert_called_once()

    finally:
        teardown_client()


def test_deactivate_inactive_academic_year_returns_400():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year(is_active=False)

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.deactivate",
            side_effect=ValueError(
                "Academic year is already inactive."
            ),
        ):
            response = client.post(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/deactivate"
            )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Academic year is already inactive."
        )

    finally:
        teardown_client()


def test_deactivate_requires_trust_access():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))
    academic_year = make_academic_year()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.academic_year.AcademicYearService.get_by_id",
            return_value=academic_year,
        ), patch(
            "app.api.v1.academic_year.has_trust_access",
            return_value=False,
        ):
            response = client.post(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/deactivate"
            )

        assert response.status_code == 403

    finally:
        teardown_client()


def test_set_current_requires_permission():
    client, _ = setup_client(make_user(trust_id=TRUST_ID))

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.post(
                f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/set-current"
            )

        assert response.status_code == 403

    finally:
        teardown_client()

def test_attach_school_to_academic_year():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year()
    school = make_school(trust_id=TRUST_ID)

    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.has_school_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch("app.api.v1.academic_year.AcademicYearService.attach_school", return_value=SchoolAcademicYear(school_id=SCHOOL_ID, academic_year_id=ACADEMIC_YEAR_ID)):
        response = client.post(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools",
            json={"school_id": str(SCHOOL_ID)},
        )

    assert response.status_code == 201
    teardown_client()


def test_attach_school_duplicate_returns_409():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year()
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.has_school_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch(
             "app.api.v1.academic_year.AcademicYearService.attach_school",
             side_effect=ValueError("School is already attached to this academic year."),
         ):
        response = client.post(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools",
            json={"school_id": str(SCHOOL_ID)},
        )

    assert response.status_code == 409
    teardown_client()


def test_attach_school_inactive_academic_year_returns_409():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year(is_active=False)
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.has_school_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch(
             "app.api.v1.academic_year.AcademicYearService.attach_school",
             side_effect=ValueError("Inactive academic year cannot have schools attached."),
         ):
        response = client.post(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools",
            json={"school_id": str(SCHOOL_ID)},
        )

    assert response.status_code == 409
    teardown_client()


def test_attach_school_missing_school_returns_404():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year()
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.has_school_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch(
             "app.api.v1.academic_year.AcademicYearService.attach_school",
             side_effect=LookupError("School not found."),
         ):
        response = client.post(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools",
            json={"school_id": str(SCHOOL_ID)},
        )

    assert response.status_code == 404
    teardown_client()


def test_attach_school_cross_trust_returns_403():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year(trust_id=TRUST_ID)
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.has_school_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch(
             "app.api.v1.academic_year.AcademicYearService.attach_school",
             side_effect=PermissionError("School belongs to a different trust."),
         ):
        response = client.post(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools",
            json={"school_id": str(OTHER_SCHOOL_ID)},
        )

    assert response.status_code == 403
    teardown_client()


def test_list_academic_year_schools():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year()
    school = make_school()
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch("app.api.v1.academic_year.AcademicYearService.list_schools", return_value=[school]):
        response = client.get(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools"
        )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(SCHOOL_ID)
    teardown_client()


def test_list_academic_year_schools_requires_trust_access():
    user = make_user(trust_id=OTHER_TRUST_ID)
    academic_year = make_academic_year(trust_id=TRUST_ID)
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=False), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year):
        response = client.get(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools"
        )

    assert response.status_code == 403
    teardown_client()


def test_detach_school():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year()
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.has_school_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch("app.api.v1.academic_year.AcademicYearService.detach_school", return_value=None):
        response = client.delete(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools/{SCHOOL_ID}"
        )

    assert response.status_code == 204
    teardown_client()


def test_detach_missing_school_association_returns_404():
    user = make_user(trust_id=TRUST_ID)
    academic_year = make_academic_year()
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=True), \
         patch("app.api.v1.academic_year.has_trust_access", return_value=True), \
         patch("app.api.v1.academic_year.has_school_access", return_value=True), \
         patch("app.api.v1.academic_year.AcademicYearService.get_by_id", return_value=academic_year), \
         patch(
             "app.api.v1.academic_year.AcademicYearService.detach_school",
             side_effect=LookupError("School is not attached to this academic year."),
         ):
        response = client.delete(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools/{SCHOOL_ID}"
        )

    assert response.status_code == 404
    teardown_client()


def test_attach_school_requires_permission():
    user = make_user(trust_id=TRUST_ID)
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=False):
        response = client.post(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools",
            json={"school_id": str(SCHOOL_ID)},
        )

    assert response.status_code == 403
    teardown_client()


def test_detach_school_requires_permission():
    user = make_user(trust_id=TRUST_ID)
    client, db = setup_client(user)

    with patch("app.api.deps.has_permission", return_value=False):
        response = client.delete(
            f"/api/v1/academic-years/{ACADEMIC_YEAR_ID}/schools/{SCHOOL_ID}"
        )

    assert response.status_code == 403
    teardown_client()
