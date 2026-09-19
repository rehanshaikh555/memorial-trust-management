from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.role import Role
from app.models.student import Student
from app.models.user import User


TRUST_ID = uuid4()
SCHOOL_ID = uuid4()
OTHER_SCHOOL_ID = uuid4()
ACADEMIC_YEAR_ID = uuid4()
CLASS_ID = uuid4()
STUDENT_ID = uuid4()
DOCUMENT_ID = uuid4()
GUARDIAN_ID = uuid4()
USER_ID = uuid4()
ROLE_ID = uuid4()


def make_user(*, trust_id=TRUST_ID):
    return User(
        id=USER_ID,
        trust_id=trust_id,
        role_id=ROLE_ID,
        email="student-admin@example.com",
        password_hash="unused",
        full_name="Student Admin",
        is_active=True,
        is_verified=True,
    )


def make_role(name="SCHOOL_ADMIN"):
    return Role(
        id=ROLE_ID,
        name=name,
        description=f"{name} role",
    )


def make_student(*, status="APPLICATION_DRAFT", is_active=False):
    return Student(
        id=STUDENT_ID,
        student_id="STU-0001",
        first_name="Avesh",
        middle_name=None,
        last_name="Shaikh",
        date_of_birth=date(2005, 4, 4),
        gender="Male",
        phone="9999999999",
        email="student@example.com",
        address="Test Address",
        status=status,
        is_active=is_active,
    )


def setup_client(user=None):
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = (
        lambda: user or make_user()
    )
    return TestClient(app), db


def teardown_client():
    app.dependency_overrides.clear()


def test_student_create_requires_permission():
    client, _ = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/students",
                json={
                    "student_id": "STU-0001",
                    "first_name": "Avesh",
                    "last_name": "Shaikh",
                    "date_of_birth": "2005-04-04",
                    "school_id": str(SCHOOL_ID),
                    "academic_year_id": str(ACADEMIC_YEAR_ID),
                    "class_id": str(CLASS_ID),
                    "enrollment_date": "2026-06-01",
                    "guardians": [],
                },
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_student_create_forbidden_without_school_access():
    client, _ = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/students",
                json={
                    "student_id": "STU-0001",
                    "first_name": "Avesh",
                    "last_name": "Shaikh",
                    "date_of_birth": "2005-04-04",
                    "school_id": str(SCHOOL_ID),
                    "academic_year_id": str(ACADEMIC_YEAR_ID),
                    "class_id": str(CLASS_ID),
                    "enrollment_date": "2026-06-01",
                    "guardians": [],
                },
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_student_create_success():
    client, _ = setup_client()
    student = make_student()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.create",
            return_value=student,
        ) as create_mock:
            response = client.post(
                "/api/v1/students",
                json={
                    "student_id": "STU-0001",
                    "first_name": "Avesh",
                    "last_name": "Shaikh",
                    "date_of_birth": "2005-04-04",
                    "school_id": str(SCHOOL_ID),
                    "academic_year_id": str(ACADEMIC_YEAR_ID),
                    "class_id": str(CLASS_ID),
                    "enrollment_date": "2026-06-01",
                    "guardians": [],
                },
            )

        assert response.status_code == 201
        assert response.json()["student_id"] == "STU-0001"
        create_mock.assert_called_once()
    finally:
        teardown_client()


def test_student_get_not_found():
    client, _ = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=None,
        ):
            response = client.get(
                f"/api/v1/students/{STUDENT_ID}"
            )

        assert response.status_code == 404
    finally:
        teardown_client()


def test_student_get_forbidden_for_other_school():
    client, _ = setup_client()
    student = make_student(status="ACTIVE", is_active=True)

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=False,
        ):
            response = client.get(
                f"/api/v1/students/{STUDENT_ID}"
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_student_update_success():
    client, _ = setup_client()
    student = make_student()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.update",
            return_value=student,
        ):
            response = client.patch(
                f"/api/v1/students/{STUDENT_ID}",
                json={"phone": "8888888888"},
            )

        assert response.status_code == 200
        assert response.json()["phone"] == "9999999999"
    finally:
        teardown_client()


def test_student_submit_success():
    client, _ = setup_client()
    student = make_student()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.submit",
            return_value=student,
        ):
            response = client.post(
                f"/api/v1/students/{STUDENT_ID}/submit"
            )

        assert response.status_code == 200
    finally:
        teardown_client()


def test_student_ready_for_approval_success():
    client, _ = setup_client()
    student = make_student(status="SUBMITTED")

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.prepare_for_approval",
            return_value=student,
        ):
            response = client.post(
                f"/api/v1/students/{STUDENT_ID}/ready-for-approval"
            )

        assert response.status_code == 200
    finally:
        teardown_client()


def test_student_approve_requires_permission():
    client, _ = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.post(
                f"/api/v1/students/{STUDENT_ID}/approve"
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_student_approve_success():
    client, _ = setup_client()
    student = make_student(status="READY_FOR_APPROVAL")

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.approve",
            return_value=student,
        ):
            response = client.post(
                f"/api/v1/students/{STUDENT_ID}/approve"
            )

        assert response.status_code == 200
    finally:
        teardown_client()


def test_student_transfer_requires_target_school_access():
    client, _ = setup_client()
    student = make_student(status="ACTIVE", is_active=True)

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            side_effect=[True, False],
        ):
            response = client.post(
                f"/api/v1/students/{STUDENT_ID}/transfer",
                json={
                    "school_id": OTHER_SCHOOL_ID.__str__(),
                    "academic_year_id": str(ACADEMIC_YEAR_ID),
                    "class_id": str(CLASS_ID),
                    "enrollment_date": "2026-07-01",
                },
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_student_exit_success():
    client, _ = setup_client()
    student = make_student(status="ACTIVE", is_active=True)

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.exit_student",
            return_value=student,
        ):
            response = client.post(
                f"/api/v1/students/{STUDENT_ID}/exit",
                params={"exit_date": "2026-09-19"},
            )

        assert response.status_code == 200
    finally:
        teardown_client()


def test_student_guardian_add_success():
    client, _ = setup_client()

    from app.models.guardian import Guardian

    student = make_student()
    guardian = Guardian(
        id=GUARDIAN_ID,
        full_name="Parent One",
        relationship="Father",
        phone="9876543210",
        email="parent@example.com",
        address="Test Address",
    )

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.get_by_id",
            return_value=student,
        ), patch(
            "app.api.v1.student.StudentService.get_current_school_id",
            return_value=SCHOOL_ID,
        ), patch(
            "app.api.v1.student.has_school_access",
            return_value=True,
        ), patch(
            "app.api.v1.student.StudentService.add_guardian",
            return_value=guardian,
        ):
            response = client.post(
                f"/api/v1/students/{STUDENT_ID}/guardians",
                json={
                    "full_name": "Parent One",
                    "relationship": "Father",
                    "phone": "9876543210",
                    "email": "parent@example.com",
                    "address": "Test Address",
                    "is_primary": True,
                },
            )

        assert response.status_code == 201
        assert response.json()["full_name"] == "Parent One"
    finally:
        teardown_client()


def test_student_document_verify_requires_permission():
    client, _ = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=False,
        ):
            response = client.post(
                f"/api/v1/students/documents/{DOCUMENT_ID}/verify",
                json={"remarks": "Verified"},
            )

        assert response.status_code == 403
    finally:
        teardown_client()


def test_student_document_reject_requires_reason():
    client, _ = setup_client()

    try:
        with patch(
            "app.api.deps.has_permission",
            return_value=True,
        ):
            response = client.post(
                f"/api/v1/students/documents/{DOCUMENT_ID}/reject",
                json={"reason": ""},
            )

        assert response.status_code == 422
    finally:
        teardown_client()
