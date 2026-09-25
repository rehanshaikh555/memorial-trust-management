import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.role import Role
from app.models.school import School
from app.models.teacher import Teacher
from app.models.trust import Trust
from app.models.user import User
from app.core.security import hash_password


client = TestClient(app)


def _unique_email() -> str:
    return f"teacher-create-{uuid.uuid4().hex[:12]}@example.com"


def test_create_teacher_persists_normalized_draft_teacher():
    db = SessionLocal()

    user = None
    teacher_id = None
    password = "TeacherCreate#123"
    email = _unique_email()

    try:
        trust = db.scalar(
            select(Trust).order_by(Trust.created_at)
        )
        assert trust is not None, "No trust available for teacher test."

        school = db.scalar(
            select(School)
            .where(
                School.trust_id == trust.id,
                School.is_active.is_(True),
            )
            .order_by(School.created_at)
        )
        assert school is not None, "No active school available for teacher test."

        role = db.scalar(
            select(Role).where(Role.name == "TRUST_ADMIN")
        )
        assert role is not None, "TRUST_ADMIN role is not seeded."

        user = User(
            trust_id=trust.id,
            role_id=role.id,
            email=email,
            password_hash=hash_password(password),
            full_name="Teacher Creation Regression Test",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login.status_code == 200, login.text

        token = login.json()["tokens"]["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
        }

        teacher_code = f"REG-{uuid.uuid4().hex[:10].upper()}"
        teacher_id = teacher_code

        response = client.post(
            "/api/v1/teachers",
            headers=headers,
            json={
                "school_id": str(school.id),
                "teacher_id": f"  {teacher_code}  ",
                "first_name": "  Regression  ",
                "last_name": "Teacher",
                "qualification": "B.Ed",
            },
        )

        assert response.status_code == 201, response.text

        payload = response.json()

        assert payload["teacher_id"] == teacher_code
        assert payload["first_name"] == "Regression"
        assert payload["status"] == "APPLICATION_DRAFT"
        assert payload["is_active"] is False

        persisted = db.scalar(
            select(Teacher).where(
                Teacher.teacher_id == teacher_code
            )
        )

        assert persisted is not None
        assert persisted.school_id == school.id
        assert persisted.teacher_id == teacher_code
        assert persisted.first_name == "Regression"
        assert persisted.status == "APPLICATION_DRAFT"
        assert persisted.is_active is False

    finally:
        cleanup = SessionLocal()

        try:
            if teacher_id is not None:
                teacher = cleanup.scalar(
                    select(Teacher).where(
                        Teacher.teacher_id == teacher_id
                    )
                )

                if teacher is not None:
                    cleanup.delete(teacher)

            if user is not None:
                persisted_user = cleanup.scalar(
                    select(User).where(User.id == user.id)
                )

                if persisted_user is not None:
                    cleanup.delete(persisted_user)

            cleanup.commit()

        finally:
            cleanup.close()
            db.close()
