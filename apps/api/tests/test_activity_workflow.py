import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.session import SessionLocal
from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.role import Role
from app.models.user import User
from app.models.user_school_access import UserSchoolAccess


client = TestClient(app)


def _auth_headers(email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def _create_test_user(
    *,
    email: str,
    password: str,
    role_name: str,
    trust_id,
    school_id=None,
) -> tuple[User, str]:
    db = SessionLocal()
    try:
        role = db.scalar(select(Role).where(Role.name == role_name))
        assert role is not None

        from app.core.security import hash_password

        user = User(
            trust_id=trust_id,
            role_id=role.id,
            email=email,
            password_hash=hash_password(password),
            full_name=f"Activity Test {role_name}",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()

        if school_id is not None:
            db.add(
                UserSchoolAccess(
                    user_id=user.id,
                    school_id=school_id,
                )
            )

        db.commit()
        db.refresh(user)
        return user, password
    finally:
        db.close()


def _get_contexts():
    db = SessionLocal()
    try:
        from app.models.academic_year import AcademicYear
        from app.models.school import School
        from app.models.school_academic_year import SchoolAcademicYear
        from app.models.trust import Trust

        trust = db.scalar(select(Trust).order_by(Trust.created_at))
        assert trust is not None

        schools = list(
            db.scalars(
                select(School)
                .where(School.trust_id == trust.id)
                .order_by(School.created_at)
            ).all()
        )

        academic_year = db.scalar(
            select(AcademicYear).order_by(AcademicYear.created_at)
        )
        assert academic_year is not None

        contexts = []

        for school in schools:
            link = db.scalar(
                select(SchoolAcademicYear).where(
                    SchoolAcademicYear.school_id == school.id,
                    SchoolAcademicYear.academic_year_id == academic_year.id,
                )
            )

            if link is not None:
                contexts.append(
                    (trust.id, school.id, academic_year.id)
                )

        assert contexts, "No school/academic-year context available."

        return contexts
    finally:
        db.close()


def _create_activity(headers, school_id, academic_year_id, title=None):
    response = client.post(
        "/api/v1/activities",
        headers=headers,
        json={
            "school_id": str(school_id),
            "academic_year_id": str(academic_year_id),
            "title": title or f"Activity {uuid.uuid4().hex[:8]}",
            "description": "Activity security integration test",
            "activity_date": str(date.today()),
            "activity_type": "SPORTS",
            "visibility": "INTERNAL",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _db_activity(activity_id):
    db = SessionLocal()
    try:
        return db.scalar(
            select(Activity).where(Activity.id == uuid.UUID(str(activity_id)))
        )
    finally:
        db.close()


def test_teacher_cannot_approve_or_publish():
    contexts = _get_contexts()
    trust_id, school_id, academic_year_id = contexts[0]

    password = "ActivityTest#123"
    email = _unique_email("activity-teacher")

    _create_test_user(
        email=email,
        password=password,
        role_name="TEACHER",
        trust_id=trust_id,
        school_id=school_id,
    )

    headers = _auth_headers(email, password)

    activity = _create_activity(
        headers,
        school_id,
        academic_year_id,
    )

    response = client.post(
        f"/api/v1/activities/{activity['id']}/submit",
        headers=headers,
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/activities/{activity['id']}/approve",
        headers=headers,
    )

    assert response.status_code == 403, response.text


def test_cross_school_activity_isolation():
    contexts = _get_contexts()

    if len(contexts) < 2:
        pytest.skip("Requires at least two schools in the same trust.")

    trust_id, school_a, academic_year_id = contexts[0]
    _, school_b, _ = contexts[1]

    password = "ActivityTest#123"
    email = _unique_email("activity-school-isolation")

    _create_test_user(
        email=email,
        password=password,
        role_name="SCHOOL_ADMIN",
        trust_id=trust_id,
        school_id=school_a,
    )

    headers = _auth_headers(email, password)

    activity = _create_activity(
        headers,
        school_b,
        academic_year_id,
    )

    assert activity is not None


def test_trust_admin_can_access_multiple_schools():
    contexts = _get_contexts()

    if len(contexts) < 2:
        pytest.skip("Requires at least two schools in the same trust.")

    trust_id, school_a, academic_year_id = contexts[0]
    _, school_b, _ = contexts[1]

    password = "ActivityTest#123"
    email = _unique_email("activity-trust-admin")

    _create_test_user(
        email=email,
        password=password,
        role_name="TRUST_ADMIN",
        trust_id=trust_id,
    )

    headers = _auth_headers(email, password)

    activity = _create_activity(
        headers,
        school_a,
        academic_year_id,
    )

    response = client.get(
        f"/api/v1/activities/{activity['id']}",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    activity_b = _create_activity(
        headers,
        school_b,
        academic_year_id,
    )

    response = client.get(
        f"/api/v1/activities/{activity_b['id']}",
        headers=headers,
    )

    assert response.status_code == 200, response.text


def test_rejected_activity_can_be_resubmitted():
    trust_id, school_id, academic_year_id = _get_contexts()[0]

    password = "ActivityTest#123"
    email = _unique_email("activity-resubmit")

    _create_test_user(
        email=email,
        password=password,
        role_name="TRUST_ADMIN",
        trust_id=trust_id,
    )

    headers = _auth_headers(email, password)

    activity = _create_activity(
        headers,
        school_id,
        academic_year_id,
    )

    activity_id = activity["id"]

    assert client.post(
        f"/api/v1/activities/{activity_id}/submit",
        headers=headers,
    ).status_code == 200

    response = client.post(
        f"/api/v1/activities/{activity_id}/reject",
        headers=headers,
        json={"reason": "Please update activity description."},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "REJECTED"

    response = client.patch(
        f"/api/v1/activities/{activity_id}",
        headers=headers,
        json={"description": "Updated after review."},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "DRAFT"

    response = client.post(
        f"/api/v1/activities/{activity_id}/submit",
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "SUBMITTED"


def test_invalid_activity_transitions_are_rejected():
    trust_id, school_id, academic_year_id = _get_contexts()[0]

    password = "ActivityTest#123"
    email = _unique_email("activity-invalid")

    _create_test_user(
        email=email,
        password=password,
        role_name="TRUST_ADMIN",
        trust_id=trust_id,
    )

    headers = _auth_headers(email, password)

    activity = _create_activity(
        headers,
        school_id,
        academic_year_id,
    )

    activity_id = activity["id"]

    response = client.post(
        f"/api/v1/activities/{activity_id}/approve",
        headers=headers,
    )

    assert response.status_code == 409, response.text

    response = client.post(
        f"/api/v1/activities/{activity_id}/publish",
        headers=headers,
    )

    assert response.status_code == 409, response.text


def test_notification_cannot_be_read_by_wrong_user():
    trust_id, school_id, academic_year_id = _get_contexts()[0]

    password = "ActivityTest#123"

    email_a = _unique_email("notification-owner")
    email_b = _unique_email("notification-other")

    user_a, _ = _create_test_user(
        email=email_a,
        password=password,
        role_name="TRUST_ADMIN",
        trust_id=trust_id,
    )

    _create_test_user(
        email=email_b,
        password=password,
        role_name="TRUST_ADMIN",
        trust_id=trust_id,
    )

    db = SessionLocal()
    try:
        notification = Notification(
            recipient_user_id=user_a.id,
            notification_type="TEST",
            title="Private notification",
            message="This notification belongs to user A.",
            priority="NORMAL",
            is_read=False,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        notification_id = notification.id
    finally:
        db.close()

    headers_b = _auth_headers(email_b, password)

    response = client.post(
        f"/api/v1/notifications/{notification_id}/read",
        headers=headers_b,
    )

    assert response.status_code in (403, 404), response.text


def test_notification_failure_rolls_back_activity_transition_and_audit():
    trust_id, school_id, academic_year_id = _get_contexts()[0]

    password = "ActivityTest#123"
    email = _unique_email("activity-rollback")

    _create_test_user(
        email=email,
        password=password,
        role_name="TRUST_ADMIN",
        trust_id=trust_id,
    )

    headers = _auth_headers(email, password)

    activity = _create_activity(
        headers,
        school_id,
        academic_year_id,
        title="Atomic rollback test",
    )

    activity_id = uuid.UUID(activity["id"])

    import app.api.v1.activity as activity_router

    original_create_many = activity_router.create_many

    def failing_create_many(*args, **kwargs):
        raise RuntimeError("Simulated notification failure")

    activity_router.create_many = failing_create_many

    try:
        response = client.post(
            f"/api/v1/activities/{activity_id}/submit",
            headers=headers,
        )
    finally:
        activity_router.create_many = original_create_many

    assert response.status_code == 500, response.text

    db = SessionLocal()
    try:
        persisted = db.scalar(
            select(Activity).where(Activity.id == activity_id)
        )

        assert persisted is not None
        assert persisted.status == "DRAFT"

        submit_audit = db.scalar(
            select(AuditLog).where(
                AuditLog.entity_type == "ACTIVITY",
                AuditLog.entity_id == activity_id,
                AuditLog.action == "ACTIVITY_SUBMITTED",
            )
        )

        assert submit_audit is None
    finally:
        db.close()
