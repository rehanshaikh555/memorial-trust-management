from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.academic_year import AcademicYear
from app.models.attendance import Attendance
from app.models.attendance_correction import AttendanceCorrection
from app.models.audit_log import AuditLog
from app.models.class_model import Class
from app.models.document_verification import DocumentVerification
from app.models.enrollment import Enrollment
from app.models.role import Role
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear
from app.models.student import Student
from app.models.student_document import StudentDocument
from app.models.trust import Trust
from app.models.user import User

from app.schemas.trust import TrustCreate
from app.schemas.school import SchoolCreate
from app.schemas.class_model import ClassCreate

from app.services import (
    academic_year_service,
    attendance_service,
    class_service,
    school_service,
    student_service,
    trust_service,
)

db = SessionLocal()
ids = {}

try:
    print("=== 1 SUPER ADMIN ===")

    role = db.scalar(select(Role).where(Role.name == "SUPER_ADMIN"))
    assert role, "SUPER_ADMIN role missing"

    admin = db.scalar(
        select(User).where(
            User.role_id == role.id,
            User.is_active.is_(True),
        ).limit(1)
    )
    assert admin, "SUPER_ADMIN user missing"

    reviewer = User(
        id=uuid4(),
        trust_id=None,
        role_id=role.id,
        email=f"integration-reviewer-{uuid4().hex[:8]}@example.com",
        password_hash="integration-test-only",
        full_name="Integration Reviewer",
        is_active=True,
        is_verified=True,
    )
    db.add(reviewer)
    db.flush()
    ids["reviewer"] = reviewer.id

    print("PASS:", admin.email)

    print("=== 2 TRUST ===")

    trust = trust_service.TrustService.create(
        db,
        TrustCreate(
            name=f"Integration Trust {uuid4().hex[:8]}",
            code=f"IT{uuid4().hex[:8].upper()}",
        ),
    )
    ids["trust"] = trust.id
    print("PASS")

    print("=== 3 SCHOOL ===")

    school = school_service.SchoolService.create(
        db,
        SchoolCreate(
            trust_id=trust.id,
            name=f"Integration School {uuid4().hex[:8]}",
            code=f"IS{uuid4().hex[:8].upper()}",
        ),
    )
    ids["school"] = school.id
    print("PASS")

    print("=== 4 CURRENT ACADEMIC YEAR ===")

    year_num = date.today().year

    year = academic_year_service.create(
        db,
        trust.id,
        f"Integration AY {year_num}",
        date(year_num, 1, 1),
        date(year_num, 12, 31),
        True,
    )

    ids["year"] = year.id
    assert year.is_current is True
    print("PASS")

    print("=== 5 SCHOOL-YEAR ===")

    sy = academic_year_service.attach_school(
        db,
        year,
        school.id,
    )

    ids["sy"] = True
    print("PASS")

    print("=== 6 CLASS ===")

    cls = class_service.create(
        db,
        ClassCreate(
            school_id=school.id,
            academic_year_id=year.id,
            name="Integration Class",
            grade_level="1",
            section="A",
        ),
    )

    ids["class"] = cls.id
    print("PASS")

    print("=== 7 STUDENT ===")

    student = student_service.create(
        db,
        actor_user_id=admin.id,
        student_id=f"INT-STU-{uuid4().hex[:10].upper()}",
        first_name="Integration",
        middle_name=None,
        last_name="Student",
        date_of_birth=date(2018, 1, 1),
        gender="MALE",
        phone=None,
        email=None,
        address=None,
        school_id=school.id,
        academic_year_id=year.id,
        class_id=cls.id,
        enrollment_date=date(year_num, 1, 2),
        guardians=[
            {
                "full_name": "Integration Guardian",
                "relationship": "FATHER",
                "phone": "9000000001",
                "email": None,
                "address": None,
                "is_primary": True,
            }
        ],
    )

    ids["student"] = student.id
    print("PASS")

    print("=== 8 SUBMIT ===")

    student_service.submit(
        db,
        student,
        actor_user_id=admin.id,
    )
    print("PASS")

    print("=== 9 DOCUMENT ===")

    doc = student_service.add_document(
        db,
        student,
        actor_user_id=admin.id,
        document_type="BIRTH_CERTIFICATE",
        file_name="integration-birth-certificate.pdf",
        storage_path="integration/student/birth-certificate.pdf",
        mime_type="application/pdf",
        file_size=1024,
        expiry_date=None,
    )

    ids["doc"] = doc.id
    print("PASS")

    print("=== 10 VERIFY DOCUMENT ===")

    student_service.verify_document(
        db,
        doc,
        actor_user_id=admin.id,
        remarks="Integration verification",
    )
    print("PASS")

    print("=== 11 PREPARE APPROVAL ===")

    student_service.prepare_for_approval(
        db,
        student,
        actor_user_id=admin.id,
    )
    print("PASS")

    print("=== 12 APPROVE STUDENT ===")

    student = student_service.approve(
        db,
        student,
        actor_user_id=admin.id,
    )

    assert student.is_active is True
    print("PASS")

    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.school_id == school.id,
            Enrollment.academic_year_id == year.id,
        )
    )

    assert enrollment
    ids["enrollment"] = enrollment.id

    attendance_date = date(year_num, 1, 6)

    while attendance_date.weekday() >= 5:
        attendance_date += timedelta(days=1)

    print("=== 13 ATTENDANCE SHEET ===")

    sheet = attendance_service.get_sheet(
        db,
        school_id=school.id,
        academic_year_id=year.id,
        class_id=cls.id,
        attendance_date=attendance_date,
        actor=admin,
    )

    assert len(sheet["items"]) == 1
    print("PASS")

    print("=== 14 BULK ATTENDANCE ===")

    attendance_service.bulk_mark(
        db,
        school_id=school.id,
        academic_year_id=year.id,
        class_id=cls.id,
        attendance_date=attendance_date,
        entries=[
            {
                "enrollment_id": enrollment.id,
                "status": "ABSENT",
                "remarks": "Integration test",
            }
        ],
        actor=admin,
    )

    print("PASS")

    print("=== 15 DUPLICATE PROTECTION ===")

    try:
        attendance_service.bulk_mark(
            db,
            school_id=school.id,
            academic_year_id=year.id,
            class_id=cls.id,
            attendance_date=attendance_date,
            entries=[
                {
                    "enrollment_id": enrollment.id,
                    "status": "PRESENT",
                }
            ],
            actor=admin,
        )
        raise AssertionError("Duplicate attendance accepted")
    except ValueError:
        print("PASS")

    attendance = db.scalar(
        select(Attendance).where(
            Attendance.enrollment_id == enrollment.id,
            Attendance.attendance_date == attendance_date,
        )
    )
    assert attendance

    print("=== 16 CORRECTION REQUEST ===")

    correction = attendance_service.request_correction(
        db,
        attendance_id=attendance.id,
        requested_status="PRESENT",
        requested_remarks="Corrected",
        reason="Integration correction",
        actor=admin,
    )

    ids["correction"] = correction.id
    print("PASS")

    print("=== 17 CORRECTION SELF-APPROVAL BLOCK ===")

    try:
        attendance_service.approve_correction(
            db,
            actor=admin,
            correction_id=correction.id,
            review_remarks="Should be blocked",
        )
        raise AssertionError(
            "Correction requester was allowed to approve their own correction."
        )
    except PermissionError:
        print("PASS")

    print("=== 18 CORRECTION APPROVAL ===")

    correction = attendance_service.approve_correction(
        db,
        actor=reviewer,
        correction_id=correction.id,
        review_remarks="Approved by separate reviewer",
    )

    assert correction.status == "APPROVED"
    assert correction.reviewed_by == reviewer.id

    print("PASS")
    print("=== 19 AUDIT ===")

    audit = db.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == attendance.id
        ).limit(1)
    )

    assert audit
    print("PASS")

    print("=== 20 MONTHLY REPORT ===")

    monthly = attendance_service.monthly_report(
        db,
        school_id=school.id,
        academic_year_id=year.id,
        class_id=cls.id,
        year_number=attendance_date.year,
        month=attendance_date.month,
        actor=admin,
    )

    assert monthly
    print("PASS")

    print("=== 21 YEARLY REPORT ===")

    yearly = attendance_service.yearly_report(
        db,
        school_id=school.id,
        academic_year_id=year.id,
        class_id=cls.id,
        actor=admin,
    )

    assert yearly
    print("PASS")

    print("")
    print("==========================================")
    print("FULL INTEGRATION FLOW PASSED")
    print("TRUST -> SCHOOL -> YEAR -> CLASS -> STUDENT")
    print("-> DOCUMENT -> APPROVAL -> ATTENDANCE")
    print("-> CORRECTION -> AUDIT -> REPORTS")
    print("==========================================")

except Exception:
    print("")
    print("INTEGRATION FLOW FAILED")
    raise

finally:
    print("=== CLEANUP ===")
    db.rollback()

    if ids.get("correction"):
        db.execute(
            delete(AttendanceCorrection).where(
                AttendanceCorrection.id == ids["correction"]
            )
        )

    if ids.get("reviewer"):
        db.execute(
            delete(User).where(
                User.id == ids["reviewer"]
            )
        )

    if ids.get("enrollment"):
        db.execute(
            delete(Attendance).where(
                Attendance.enrollment_id == ids["enrollment"]
            )
        )

    if ids.get("doc"):
        db.execute(
            delete(DocumentVerification).where(
                DocumentVerification.document_id == ids["doc"]
            )
        )
        db.execute(
            delete(StudentDocument).where(
                StudentDocument.id == ids["doc"]
            )
        )

    if ids.get("student"):
        db.execute(
            delete(Enrollment).where(
                Enrollment.student_id == ids["student"]
            )
        )
        db.execute(
            delete(AuditLog).where(
                AuditLog.entity_id == ids["student"]
            )
        )
        db.execute(
            delete(Student).where(
                Student.id == ids["student"]
            )
        )

    if ids.get("class"):
        db.execute(
            delete(Class).where(
                Class.id == ids["class"]
            )
        )

    if ids.get("sy"):
        db.execute(
            delete(SchoolAcademicYear).where(
                SchoolAcademicYear.school_id == ids["school"],
                SchoolAcademicYear.academic_year_id == ids["year"],
            )
        )

    if ids.get("year"):
        db.execute(
            delete(AcademicYear).where(
                AcademicYear.id == ids["year"]
            )
        )

    if ids.get("school"):
        db.execute(
            delete(School).where(
                School.id == ids["school"]
            )
        )

    if ids.get("trust"):
        db.execute(
            delete(Trust).where(
                Trust.id == ids["trust"]
            )
        )

    db.commit()
    db.close()
    print("Cleanup complete.")



























