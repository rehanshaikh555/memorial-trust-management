from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app


def make_user(role_name="SCHOOL_ADMIN", trust_id=None):
    return SimpleNamespace(
        id=uuid4(),
        trust_id=trust_id or uuid4(),
        role_id=uuid4(),
        email="class-test@example.com",
        full_name="Class Test User",
        is_active=True,
        is_verified=True,
    )


def make_class():
    return SimpleNamespace(
        id=uuid4(),
        school_id=uuid4(),
        academic_year_id=uuid4(),
        name="Grade 5 A",
        grade_level=5,
        section="A",
        is_active=True,
    )


def setup_client(user=None):
    db = MagicMock()
    current_user = user or make_user()

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: current_user

    return TestClient(app), db, current_user


def teardown_client():
    app.dependency_overrides.clear()


def test_class_create_requires_permission():
    client, db, user = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/classes",
                json={
                    "school_id": str(uuid4()),
                    "academic_year_id": str(uuid4()),
                    "name": "Grade 5 A",
                    "grade_level": 5,
                    "section": "A",
                },
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_class_create_forbidden_without_school_access():
    client, db, user = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.has_school_access",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/classes",
                json={
                    "school_id": str(uuid4()),
                    "academic_year_id": str(uuid4()),
                    "name": "Grade 5 A",
                    "grade_level": 5,
                    "section": "A",
                },
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_class_create_success():
    client, db, user = setup_client()

    school_id = uuid4()
    academic_year_id = uuid4()
    class_record = make_class()
    class_record.school_id = school_id
    class_record.academic_year_id = academic_year_id

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.create",
            return_value=class_record,
        ):
            response = client.post(
                "/api/v1/classes",
                json={
                    "school_id": str(school_id),
                    "academic_year_id": str(academic_year_id),
                    "name": "Grade 5 A",
                    "grade_level": 5,
                    "section": "A",
                },
            )

        assert response.status_code == 201
        assert response.json()["name"] == "Grade 5 A"
    finally:
        teardown_client()


def test_class_list_rejects_unscoped_school():
    client, db, user = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.get_user_role",
            return_value=SimpleNamespace(name="SCHOOL_ADMIN"),
        ), patch(
            "app.api.v1.class_model.has_school_access",
            return_value=False,
        ):
            response = client.get(
                f"/api/v1/classes?school_id={uuid4()}"
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_class_get_not_found():
    client, db, user = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.get_by_id",
            return_value=None,
        ):
            response = client.get(
                f"/api/v1/classes/{uuid4()}"
            )

        assert response.status_code == 404
    finally:
        teardown_client()


def test_class_get_forbidden_without_school_access():
    client, db, user = setup_client()
    class_record = make_class()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.get_by_id",
            return_value=class_record,
        ), patch(
            "app.api.v1.class_model.has_school_access",
            return_value=False,
        ):
            response = client.get(
                f"/api/v1/classes/{class_record.id}"
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_class_get_success():
    client, db, user = setup_client()
    class_record = make_class()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.get_by_id",
            return_value=class_record,
        ), patch(
            "app.api.v1.class_model.has_school_access",
            return_value=True,
        ):
            response = client.get(
                f"/api/v1/classes/{class_record.id}"
            )

        assert response.status_code == 200
        assert response.json()["grade_level"] == 5
    finally:
        teardown_client()


def test_class_update_success():
    client, db, user = setup_client()
    class_record = make_class()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.get_by_id",
            return_value=class_record,
        ), patch(
            "app.api.v1.class_model.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.update",
            return_value=class_record,
        ):
            response = client.patch(
                f"/api/v1/classes/{class_record.id}",
                json={"name": "Grade 5 Updated"},
            )

        assert response.status_code == 200
    finally:
        teardown_client()


def test_class_deactivate_success():
    client, db, user = setup_client()
    class_record = make_class()
    class_record.is_active = False

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.get_by_id",
            return_value=class_record,
        ), patch(
            "app.api.v1.class_model.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.deactivate",
            return_value=class_record,
        ):
            response = client.post(
                f"/api/v1/classes/{class_record.id}/deactivate"
            )

        assert response.status_code == 200
    finally:
        teardown_client()


def test_class_list_school_admin_is_school_scoped():
    client, db, user = setup_client()
    school_id = uuid4()

    try:
        role = SimpleNamespace(name="SCHOOL_ADMIN")

        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.class_model.get_user_role",
            return_value=role,
        ):
            response = client.get(
                f"/api/v1/classes?school_id={school_id}"
            )

        assert response.status_code == 403
    finally:
        teardown_client()
