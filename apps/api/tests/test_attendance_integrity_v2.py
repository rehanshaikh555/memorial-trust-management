from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.academic_year import AcademicYear
from app.models.attendance import Attendance
from app.models.attendance_correction import AttendanceCorrection
from app.models.audit_log import AuditLog
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.models.trust import Trust
from app.models.user import User
from app.models.user_school_access import UserSchoolAccess

from app.services import academic_year_service
from app.services import attendance_service
from app.services import class_service
from app.services import school_service
from app.services import student_service
from app.services import trust_service
from app.schemas.class_model import ClassCreate
from app.schemas.school import SchoolCreate
from app.schemas.trust import TrustCreate


def _role(db, name):
    from app.models.role import Role

    role = db.scalar(select(Role).where(Role.name == name))
    assert role is not None, f"Required role missing: {name}"
    return role


def _new_user(db, *, role_name, trust_id=None, school_id=None, label="user"):
    role = _role(db, role_name)

    user = User(
        id=uuid4(),
        trust_id=trust_id,
        role_id=role.id,
        email=f"attendance-v2-{label}-{uuid4().hex[:10]}@example.com",
        password_hash="attendance-v2-test-only",
        full_name=f"Attendance V2 {label}",
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
        db.flush()

    return user


@pytest.fixture
def attendance_case():
    db = SessionLocal()
    created = {
        "trust": None,
        "schools": [],
        "years": [],
        "classes": [],
        "students": [],
        "enrollments": [],
        "teachers": [],
        "users": [],
        "assignments": [],
    }

    try:
        super_admin_role = _role(db, "SUPER_ADMIN")

        super_admin = db.scalar(
            select(User)
            .where(
                User.role_id == super_admin_role.id,
                User.is_active.is_(True),
            )
            .limit(1)
        )
        assert super_admin is not None
        created["users"].append(super_admin.id)

        trust = trust_service.TrustService.create(
            db,
            TrustCreate(
                name=f"Attendance V2 Trust {uuid4().hex[:8]}",
                code=f"AV2{uuid4().hex[:8].upper()}",
            ),
        )
        created["trust"] = trust.id

        school_a = school_service.SchoolService.create(
            db,
            SchoolCreate(
                trust_id=trust.id,
                name=f"Attendance V2 School A {uuid4().hex[:8]}",
                code=f"AV2A{uuid4().hex[:8].upper()}",
            ),
        )

        school_b = school_service.SchoolService.create(
            db,
            SchoolCreate(
                trust_id=trust.id,
                name=f"Attendance V2 School B {uuid4().hex[:8]}",
                code=f"AV2B{uuid4().hex[:8].upper()}",
            ),
        )

        created["schools"] += [school_a.id, school_b.id]

        year_number = date.today().year
        year = academic_year_service.create(
            db,
            trust.id,
            f"AttV2 {uuid4().hex[:8]}",
            date(year_number, 1, 1),
            date(year_number, 12, 31),
            True,
        )
        created["years"].append(year.id)

        academic_year_service.attach_school(db, year, school_a.id)
        academic_year_service.attach_school(db, year, school_b.id)

        class_a = class_service.create(
            db,
            ClassCreate(
                school_id=school_a.id,
                academic_year_id=year.id,
                name=f"Class A {uuid4().hex[:8]}",
                grade_level=1,
                section="A",
            ),
        )

        class_b = class_service.create(
            db,
            ClassCreate(
                school_id=school_a.id,
                academic_year_id=year.id,
                name=f"Class B {uuid4().hex[:8]}",
                grade_level=2,
                section="B",
            ),
        )

        class_other_school = class_service.create(
            db,
            ClassCreate(
                school_id=school_b.id,
                academic_year_id=year.id,
                name=f"Other School Class {uuid4().hex[:8]}",
                grade_level=1,
                section="A",
            ),
        )

        created["classes"] += [
            class_a.id,
            class_b.id,
            class_other_school.id,
        ]

        school_admin = _new_user(
            db,
            role_name="SCHOOL_ADMIN",
            trust_id=trust.id,
            school_id=school_a.id,
            label="school-admin",
        )

        teacher_user = _new_user(
            db,
            role_name="TEACHER",
            trust_id=trust.id,
            school_id=school_a.id,
            label="teacher",
        )

        other_school_user = _new_user(
            db,
            role_name="TEACHER",
            trust_id=trust.id,
            school_id=school_b.id,
            label="other-school-teacher",
        )

        created["users"] += [
            school_admin.id,
            teacher_user.id,
            other_school_user.id,
        ]

        teacher = Teacher(
            id=uuid4(),
            user_id=teacher_user.id,
            school_id=school_a.id,
            teacher_id=f"AV2-T-{uuid4().hex[:10].upper()}",
            first_name="Attendance",
            last_name="Teacher",
            status="ACTIVE",
            is_active=True,
        )
        db.add(teacher)
        db.flush()
        created["teachers"].append(teacher.id)

        other_teacher = Teacher(
            id=uuid4(),
            user_id=other_school_user.id,
            school_id=school_b.id,
            teacher_id=f"AV2-T-{uuid4().hex[:10].upper()}",
            first_name="Other",
            last_name="Teacher",
            status="ACTIVE",
            is_active=True,
        )
        db.add(other_teacher)
        db.flush()
        created["teachers"].append(other_teacher.id)

        assignment = TeacherAssignment(
            id=uuid4(),
            teacher_id=teacher.id,
            school_id=school_a.id,
            academic_year_id=year.id,
            class_id=class_a.id,
            subject="General",
            start_date=date(year_number, 1, 1),
            end_date=date(year_number, 12, 31),
            status="ACTIVE",
        )
        db.add(assignment)
        created["assignments"].append(assignment.id)

        student = student_service.create(
            db,
            actor_user_id=school_admin.id,
            student_id=f"AV2-STU-{uuid4().hex[:10].upper()}",
            first_name="Attendance",
            middle_name=None,
            last_name="Student",
            date_of_birth=date(2018, 1, 1),
            gender="MALE",
            phone=None,
            email=None,
            address=None,
            school_id=school_a.id,
            academic_year_id=year.id,
            class_id=class_a.id,
            enrollment_date=date(year_number, 1, 2),
            guardians=[
                {
                    "full_name": "Attendance Guardian",
                    "relationship": "FATHER",
                    "phone": "9000000001",
                    "email": None,
                    "address": None,
                    "is_primary": True,
                }
            ],
        )
        created["students"].append(student.id)

        enrollment = db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student.id,
                Enrollment.school_id == school_a.id,
                Enrollment.academic_year_id == year.id,
            )
        )
        assert enrollment is not None
        created["enrollments"].append(enrollment.id)

        db.commit()

        yield {
            "db": db,
            "year": year,
            "school_a": school_a,
            "school_b": school_b,
            "class_a": class_a,
            "class_b": class_b,
            "class_other_school": class_other_school,
            "school_admin": school_admin,
            "teacher_user": teacher_user,
            "other_school_user": other_school_user,
            "teacher": teacher,
            "student": student,
            "enrollment": enrollment,
            "attendance_date": date(year_number, 1, 6),
            "enrollments": created["enrollments"],
        }

    finally:
        try:
            db.rollback()

            for teacher_id in created["teachers"]:
                db.execute(
                    delete(TeacherAssignment).where(
                        TeacherAssignment.teacher_id == teacher_id
                    )
                )

            for enrollment_id in created["enrollments"]:
                db.execute(
                    delete(AttendanceCorrection).where(
                        AttendanceCorrection.attendance_id.in_(
                            select(Attendance.id).where(
                                Attendance.enrollment_id == enrollment_id
                            )
                        )
                    )
                )
                db.execute(
                    delete(Attendance).where(
                        Attendance.enrollment_id == enrollment_id
                    )
                )

            for student_id in created["students"]:
                db.execute(
                    delete(Enrollment).where(
                        Enrollment.student_id == student_id
                    )
                )
                db.execute(
                    delete(AuditLog).where(
                        AuditLog.entity_id == student_id
                    )
                )
                db.execute(
                    delete(Student).where(Student.id == student_id)
                )

            for teacher_id in created["teachers"]:
                db.execute(delete(Teacher).where(Teacher.id == teacher_id))

            for user_id in created["users"]:
                if user_id != super_admin.id if "super_admin" in locals() else True:
                    db.execute(
                        delete(UserSchoolAccess).where(
                            UserSchoolAccess.user_id == user_id
                        )
                    )

            for user_id in created["users"]:
                if "super_admin" not in locals() or user_id != super_admin.id:
                    db.execute(delete(User).where(User.id == user_id))

            for class_id in created["classes"]:
                db.execute(delete(Class).where(Class.id == class_id))

            for school_id in created["schools"]:
                db.execute(
                    delete(SchoolAcademicYear).where(
                        SchoolAcademicYear.school_id == school_id
                    )
                )

            for year_id in created["years"]:
                db.execute(
                    delete(AcademicYear).where(AcademicYear.id == year_id)
                )

            for school_id in created["schools"]:
                db.execute(delete(School).where(School.id == school_id))

            if created["trust"] is not None:
                db.execute(
                    delete(Trust).where(Trust.id == created["trust"])
                )

            db.commit()
        finally:
            db.close()


def _mark(
    case,
    *,
    actor,
    status="PRESENT",
    attendance_date=None,
    class_id=None,
):
    return attendance_service.bulk_mark(
        case["db"],
        actor=actor,
        school_id=case["school_a"].id,
        academic_year_id=case["year"].id,
        class_id=class_id or case["class_a"].id,
        attendance_date=attendance_date or case["attendance_date"],
        entries=[
            {
                "enrollment_id": case["enrollment"].id,
                "status": status,
                "remarks": None,
            }
        ],
    )


def test_teacher_cannot_mark_another_class(attendance_case):
    with pytest.raises(PermissionError):
        _mark(
            attendance_case,
            actor=attendance_case["teacher_user"],
            class_id=attendance_case["class_b"].id,
        )


def test_teacher_cannot_mark_another_school(attendance_case):
    with pytest.raises(PermissionError):
        attendance_service.bulk_mark(
            attendance_case["db"],
            actor=attendance_case["teacher_user"],
            school_id=attendance_case["school_b"].id,
            academic_year_id=attendance_case["year"].id,
            class_id=attendance_case["class_other_school"].id,
            attendance_date=attendance_case["attendance_date"],
            entries=[],
        )


def test_teacher_cannot_read_another_class(attendance_case):
    rows = attendance_service.list_attendance(
        attendance_case["db"],
        actor=attendance_case["teacher_user"],
        school_id=attendance_case["school_a"].id,
        academic_year_id=attendance_case["year"].id,
        class_id=attendance_case["class_b"].id,
    )
    assert rows == []


def test_teacher_report_cannot_escape_assigned_class(attendance_case):
    with pytest.raises(PermissionError):
        attendance_service.monthly_report(
            attendance_case["db"],
            actor=attendance_case["teacher_user"],
            school_id=attendance_case["school_a"].id,
            academic_year_id=attendance_case["year"].id,
            month=attendance_case["attendance_date"].month,
            year_number=attendance_case["attendance_date"].year,
            class_id=attendance_case["class_b"].id,
        )


def test_attendance_date_must_be_inside_academic_year(attendance_case):
    outside = attendance_case["year"].end_date + timedelta(days=1)

    with pytest.raises(ValueError, match="academic year"):
        _mark(
            attendance_case,
            actor=attendance_case["school_admin"],
            attendance_date=outside,
        )


def test_non_working_calendar_day_rejects_attendance(attendance_case):
    db = attendance_case["db"]
    day = attendance_case["attendance_date"]

    from app.models.school_calendar import SchoolCalendar

    db.add(
        SchoolCalendar(
            id=uuid4(),
            school_id=attendance_case["school_a"].id,
            academic_year_id=attendance_case["year"].id,
            calendar_date=day,
            is_working_day=False,
            day_type="HOLIDAY",
            holiday_name="Test Holiday",
            remarks=None,
        )
    )
    db.commit()

    with pytest.raises(ValueError, match="working day"):
        _mark(
            attendance_case,
            actor=attendance_case["school_admin"],
            attendance_date=day,
        )


def test_inactive_student_attendance_remains_reportable(attendance_case):
    db = attendance_case["db"]

    _mark(
        attendance_case,
        actor=attendance_case["school_admin"],
        status="PRESENT",
    )

    student = db.get(Student, attendance_case["student"].id)
    student.is_active = False
    db.commit()

    rows = attendance_service.list_attendance(
        db,
        actor=attendance_case["school_admin"],
        school_id=attendance_case["school_a"].id,
        academic_year_id=attendance_case["year"].id,
        student_id=attendance_case["student"].id,
    )

    assert len(rows) == 1
    assert rows[0]["student_id"] == attendance_case["student"].id


def test_correction_requester_cannot_self_approve(attendance_case):
    db = attendance_case["db"]

    attendance = _mark(
        attendance_case,
        actor=attendance_case["school_admin"],
    )[0]

    correction = attendance_service.request_correction(
        db,
        actor=attendance_case["teacher_user"],
        attendance_id=attendance.id,
        requested_status="ABSENT",
        requested_remarks="Correction required",
        reason="Original attendance was incorrect.",
    )

    with pytest.raises(PermissionError, match="cannot review"):
        attendance_service.approve_correction(
            db,
            actor=attendance_case["teacher_user"],
            correction_id=correction.id,
            review_remarks="Attempted self approval",
        )


def test_stale_correction_cannot_overwrite_newer_attendance(attendance_case):
    db = attendance_case["db"]

    attendance = _mark(
        attendance_case,
        actor=attendance_case["school_admin"],
        status="PRESENT",
    )[0]

    correction = attendance_service.request_correction(
        db,
        actor=attendance_case["teacher_user"],
        attendance_id=attendance.id,
        requested_status="ABSENT",
        requested_remarks=None,
        reason="Correction request",
    )

    attendance.status = "LATE"
    attendance.remarks = "Updated independently."
    db.commit()

    with pytest.raises(ValueError, match="changed"):
        attendance_service.approve_correction(
            db,
            actor=attendance_case["school_admin"],
            correction_id=correction.id,
            review_remarks="Approve stale request",
        )

    db.refresh(attendance)
    assert attendance.status == "LATE"


def test_correction_reviewer_must_have_school_scope(attendance_case):
    db = attendance_case["db"]

    attendance = _mark(
        attendance_case,
        actor=attendance_case["school_admin"],
    )[0]

    correction = attendance_service.request_correction(
        db,
        actor=attendance_case["teacher_user"],
        attendance_id=attendance.id,
        requested_status="ABSENT",
        requested_remarks=None,
        reason="Correction request",
    )

    with pytest.raises(PermissionError):
        attendance_service.approve_correction(
            db,
            actor=attendance_case["other_school_user"],
            correction_id=correction.id,
            review_remarks="Cross school approval attempt",
        )


def test_transfer_history_preserves_previous_attendance(attendance_case):
    db = attendance_case["db"]

    old_date = attendance_case["attendance_date"]
    new_date = old_date + timedelta(days=5)

    old_attendance = _mark(
        attendance_case,
        actor=attendance_case["school_admin"],
        status="PRESENT",
        attendance_date=old_date,
    )[0]

    enrollment = db.get(Enrollment, attendance_case["enrollment"].id)
    enrollment.exit_date = old_date
    enrollment.status = "TRANSFERRED"
    db.commit()

    new_enrollment = Enrollment(
        id=uuid4(),
        student_id=attendance_case["student"].id,
        school_id=attendance_case["school_a"].id,
        academic_year_id=attendance_case["year"].id,
        class_id=attendance_case["class_b"].id,
        enrollment_date=new_date,
        exit_date=None,
        status="ACTIVE",
    )
    db.add(new_enrollment)
    db.commit()
    attendance_case["enrollments"].append(new_enrollment.id)

    created = attendance_service.bulk_mark(
        db,
        actor=attendance_case["school_admin"],
        school_id=attendance_case["school_a"].id,
        academic_year_id=attendance_case["year"].id,
        class_id=attendance_case["class_b"].id,
        attendance_date=new_date,
        entries=[
            {
                "enrollment_id": new_enrollment.id,
                "status": "ABSENT",
                "remarks": None,
            }
        ],
    )

    rows = attendance_service.list_attendance(
        db,
        actor=attendance_case["school_admin"],
        school_id=attendance_case["school_a"].id,
        academic_year_id=attendance_case["year"].id,
        student_id=attendance_case["student"].id,
    )

    attendance_ids = {row["id"] for row in rows}

    assert old_attendance.id in attendance_ids
    assert created[0].id in attendance_ids


def test_calendar_access_is_school_scoped(attendance_case):
    from app.models.school_calendar import SchoolCalendar

    db = attendance_case["db"]

    record = SchoolCalendar(
        id=uuid4(),
        school_id=attendance_case["school_a"].id,
        academic_year_id=attendance_case["year"].id,
        calendar_date=attendance_case["attendance_date"],
        is_working_day=False,
        day_type="HOLIDAY",
        holiday_name="Scoped Holiday",
        remarks=None,
    )
    db.add(record)
    db.commit()

    with pytest.raises(PermissionError):
        attendance_service.update_calendar(
            db,
            actor=attendance_case["other_school_user"],
            calendar_id=record.id,
            values={"is_working_day": True},
        )
