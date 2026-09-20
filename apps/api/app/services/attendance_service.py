from calendar import monthrange
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.attendance import Attendance
from app.models.attendance_correction import AttendanceCorrection
from app.models.audit_log import AuditLog
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.school import School
from app.models.school_calendar import SchoolCalendar
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User
from app.models.role import Role
from app.models.user_school_access import UserSchoolAccess
STATUS_VALUES = {"PRESENT", "ABSENT", "LATE", "EXCUSED"}
CORRECTION_PENDING = "PENDING"
CORRECTION_APPROVED = "APPROVED"
CORRECTION_REJECTED = "REJECTED"


def _audit(
    db: Session,
    *,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    school_id: UUID | None,
    description: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            school_id=school_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
            occurred_at=datetime.now(timezone.utc),
        )
    )


def _school(db: Session, school_id: UUID) -> School:
    school = db.scalar(select(School).where(School.id == school_id))
    if school is None:
        raise LookupError("School not found.")
    if not school.is_active:
        raise ValueError("School is inactive.")
    return school


def _academic_year(db: Session, academic_year_id: UUID) -> AcademicYear:
    year = db.scalar(
        select(AcademicYear).where(AcademicYear.id == academic_year_id)
    )
    if year is None:
        raise LookupError("Academic year not found.")
    if not year.is_active:
        raise ValueError("Academic year is inactive.")
    return year


def _class(
    db: Session,
    *,
    class_id: UUID,
    school_id: UUID,
    academic_year_id: UUID,
) -> Class:
    record = db.scalar(select(Class).where(Class.id == class_id))
    if record is None:
        raise LookupError("Class not found.")
    if not record.is_active:
        raise ValueError("Class is inactive.")
    if record.school_id != school_id or record.academic_year_id != academic_year_id:
        raise ValueError("Class does not belong to the selected school and academic year.")
    return record


def _validate_scope(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
) -> School:
    school = _school(db, school_id)

    role = db.scalar(
        select(Role).where(Role.id == actor.role_id)
    )

    if role is None:
        raise PermissionError("User role could not be resolved.")

    role_name = role.name

    # SUPER_ADMIN has global access.
    if role_name == "SUPER_ADMIN":
        return school

    # Trust-level administrators can access every school in their trust.
    if role_name == "TRUST_ADMIN":
        if actor.trust_id != school.trust_id:
            raise PermissionError(
                "You do not have access to this school's trust."
            )
        return school

    # School-scoped roles must have an explicit school access record.
    access = db.scalar(
        select(UserSchoolAccess).where(
            UserSchoolAccess.user_id == actor.id,
            UserSchoolAccess.school_id == school_id,
        )
    )

    if access is None:
        raise PermissionError(
            "You do not have access to this school."
        )

    return school


def _role_name(db: Session, actor: User) -> str:
    role = db.scalar(
        select(Role).where(Role.id == actor.role_id)
    )

    if role is None:
        raise PermissionError("User role could not be resolved.")

    return role.name


def _validate_teacher_class_scope(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    attendance_date: date,
) -> None:
    role_name = _role_name(db, actor)

    if role_name != "TEACHER":
        return

    teacher = db.scalar(
        select(Teacher).where(
            Teacher.user_id == actor.id,
            Teacher.school_id == school_id,
            Teacher.is_active.is_(True),
        )
    )

    if teacher is None:
        raise PermissionError(
            "Teacher is not active or does not belong to this school."
        )

    assignment = db.scalar(
        select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.school_id == school_id,
            TeacherAssignment.academic_year_id == academic_year_id,
            TeacherAssignment.status == "ACTIVE",
            (
                (TeacherAssignment.class_id == class_id)
                | TeacherAssignment.class_id.is_(None)
            ),
            TeacherAssignment.start_date <= attendance_date,
            (
                (TeacherAssignment.end_date.is_(None))
                | (TeacherAssignment.end_date >= attendance_date)
            ),
        )
    )

    if assignment is None:
        raise PermissionError(
            "Teacher is not assigned to this class for the requested attendance date."
        )


def _validate_correction_reviewer(
    db: Session,
    *,
    actor: User,
    requested_by,
    school_id: UUID,
) -> None:
    role_name = _role_name(db, actor)

    if actor.id == requested_by:
        raise PermissionError(
            "The user who requested a correction cannot review the same correction."
        )

    if role_name not in {
        "SUPER_ADMIN",
        "TRUST_ADMIN",
        "SCHOOL_ADMIN",
    }:
        raise PermissionError(
            "Only authorized administrators can review attendance corrections."
        )

    _validate_scope(
        db,
        actor=actor,
        school_id=school_id,
    )

def _calendar_record(
    db: Session,
    *,
    school_id: UUID,
    academic_year_id: UUID,
    attendance_date: date,
) -> SchoolCalendar | None:
    return db.scalar(
        select(SchoolCalendar).where(
            SchoolCalendar.school_id == school_id,
            SchoolCalendar.academic_year_id == academic_year_id,
            SchoolCalendar.calendar_date == attendance_date,
        )
    )


def _is_working_day(
    db: Session,
    *,
    school_id: UUID,
    academic_year_id: UUID,
    attendance_date: date,
) -> bool:
    record = _calendar_record(
        db,
        school_id=school_id,
        academic_year_id=academic_year_id,
        attendance_date=attendance_date,
    )

    # A missing calendar row represents a normal working day.
    return True if record is None else record.is_working_day


def _validate_date_in_year(
    year: AcademicYear,
    attendance_date: date,
) -> None:
    if attendance_date < year.start_date or attendance_date > year.end_date:
        raise ValueError("Attendance date must fall within the academic year.")


def _enrollments_for_class(
    db: Session,
    *,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    attendance_date: date,
) -> list[Enrollment]:
    statement = (
        select(Enrollment)
        .join(Student, Student.id == Enrollment.student_id)
        .where(
            Enrollment.school_id == school_id,
            Enrollment.academic_year_id == academic_year_id,
            Enrollment.class_id == class_id,
            Enrollment.enrollment_date <= attendance_date,
            (
                (Enrollment.exit_date.is_(None))
                | (Enrollment.exit_date >= attendance_date)
            ),
        )
        .order_by(Enrollment.enrollment_date, Enrollment.id)
    )

    return list(db.scalars(statement).all())


def get_sheet(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    attendance_date: date,
) -> dict:
    _validate_scope(db, actor=actor, school_id=school_id)
    year = _academic_year(db, academic_year_id)

    _validate_date_in_year(year, attendance_date)
    _class(
        db,
        class_id=class_id,
        school_id=school_id,
        academic_year_id=academic_year_id,
    )

    _validate_teacher_class_scope(
        db,
        actor=actor,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        attendance_date=attendance_date,
    )

    enrollments = _enrollments_for_class(
        db,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        attendance_date=attendance_date,
    )

    existing = {
        row.enrollment_id: row
        for row in db.scalars(
            select(Attendance).where(
                Attendance.attendance_date == attendance_date,
                Attendance.enrollment_id.in_(
                    [item.id for item in enrollments]
                )
            )
        ).all()
    }

    items = []

    for enrollment in enrollments:
        student = db.scalar(
            select(Student).where(Student.id == enrollment.student_id)
        )
        if student is None:
            continue

        record = existing.get(enrollment.id)

        items.append(
            {
                "enrollment_id": enrollment.id,
                "student_id": student.id,
                "student_code": student.student_id,
                "student_name": " ".join(
                    part for part in
                    [student.first_name, student.middle_name, student.last_name]
                    if part
                ),
                "status": record.status if record else None,
                "remarks": record.remarks if record else None,
            }
        )

    return {
        "school_id": school_id,
        "academic_year_id": academic_year_id,
        "class_id": class_id,
        "attendance_date": attendance_date,
        "is_working_day": _is_working_day(
            db,
            school_id=school_id,
            academic_year_id=academic_year_id,
            attendance_date=attendance_date,
        ),
        "items": items,
    }


def bulk_mark(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    attendance_date: date,
    entries: list[dict],
) -> list[Attendance]:
    _validate_scope(db, actor=actor, school_id=school_id)

    year = _academic_year(db, academic_year_id)
    _validate_date_in_year(year, attendance_date)

    _class(
        db,
        class_id=class_id,
        school_id=school_id,
        academic_year_id=academic_year_id,
    )

    _validate_teacher_class_scope(
        db,
        actor=actor,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        attendance_date=attendance_date,
    )

    if not _is_working_day(
        db,
        school_id=school_id,
        academic_year_id=academic_year_id,
        attendance_date=attendance_date,
    ):
        raise ValueError("Attendance cannot be marked on a non-working day.")

    enrollments = _enrollments_for_class(
        db,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        attendance_date=attendance_date,
    )

    allowed = {item.id: item for item in enrollments}

    if not allowed:
        raise ValueError("No students are enrolled in this class on the selected date.")

    submitted_ids = [entry["enrollment_id"] for entry in entries]

    if len(submitted_ids) != len(set(submitted_ids)):
        raise ValueError("Duplicate enrollment IDs were submitted.")

    if set(submitted_ids) != set(allowed):
        raise ValueError(
            "Attendance submission must contain every enrolled student exactly once."
        )

    existing = {
        row.enrollment_id: row
        for row in db.scalars(
            select(Attendance).where(
                Attendance.attendance_date == attendance_date,
                Attendance.enrollment_id.in_(list(allowed)),
            )
        ).all()
    }

    changed = []

    for entry in entries:
        enrollment_id = entry["enrollment_id"]
        status = entry["status"].upper()

        if status not in STATUS_VALUES:
            raise ValueError(
                f"Invalid attendance status: {status}."
            )

        enrollment = allowed.get(enrollment_id)
        if enrollment is None:
            raise PermissionError(
                "One or more attendance entries do not belong to the selected class."
            )

        record = existing.get(enrollment_id)

        if record is not None:
            # Existing attendance must be corrected through the correction workflow.
            raise ValueError(
                "Attendance already exists for at least one submitted student. "
                "Use attendance correction for changes."
            )

        record = Attendance(
            enrollment_id=enrollment_id,
            attendance_date=attendance_date,
            status=status,
            marked_by=actor.id,
            remarks=entry.get("remarks"),
        )

        db.add(record)
        db.flush()

        _audit(
            db,
            actor_user_id=actor.id,
            action="ATTENDANCE_MARKED",
            entity_type="ATTENDANCE",
            entity_id=record.id,
            school_id=school_id,
            new_values={
                "enrollment_id": str(enrollment_id),
                "attendance_date": str(attendance_date),
                "status": status,
            },
        )

        changed.append(record)

    try:
        db.commit()
        for record in changed:
            db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Attendance could not be saved because a record already exists."
        ) from None

    return changed


def list_attendance(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID | None = None,
    class_id: UUID | None = None,
    student_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    _validate_scope(db, actor=actor, school_id=school_id)

    role_name = _role_name(db, actor)

    statement = (
        select(Attendance, Enrollment, Student)
        .join(Enrollment, Enrollment.id == Attendance.enrollment_id)
        .join(Student, Student.id == Enrollment.student_id)
        .where(Enrollment.school_id == school_id)
    )

    if academic_year_id:
        statement = statement.where(
            Enrollment.academic_year_id == academic_year_id
        )

    if class_id:
        statement = statement.where(Enrollment.class_id == class_id)

    if student_id:
        statement = statement.where(Enrollment.student_id == student_id)

    if start_date:
        statement = statement.where(
            Attendance.attendance_date >= start_date
        )

    if end_date:
        statement = statement.where(
            Attendance.attendance_date <= end_date
        )

    statement = statement.order_by(
        Attendance.attendance_date.desc(),
        Student.last_name,
        Student.first_name,
    )

    rows = db.execute(statement).all()

    if role_name == "TEACHER":
        filtered_rows = []

        teacher = db.scalar(
            select(Teacher).where(
                Teacher.user_id == actor.id,
                Teacher.school_id == school_id,
                Teacher.is_active.is_(True),
            )
        )

        if teacher is None:
            raise PermissionError(
                "Teacher is not active or does not belong to this school."
            )

        for attendance, enrollment, student in rows:
            assignment = db.scalar(
                select(TeacherAssignment).where(
                    TeacherAssignment.teacher_id == teacher.id,
                    TeacherAssignment.school_id == school_id,
                    TeacherAssignment.academic_year_id == enrollment.academic_year_id,
                    TeacherAssignment.status == "ACTIVE",
                    (
                        (TeacherAssignment.class_id == enrollment.class_id)
                        | TeacherAssignment.class_id.is_(None)
                    ),
                    TeacherAssignment.start_date <= attendance.attendance_date,
                    (
                        (TeacherAssignment.end_date.is_(None))
                        | (
                            TeacherAssignment.end_date
                            >= attendance.attendance_date
                        )
                    ),
                )
            )

            if assignment is not None:
                filtered_rows.append(
                    (attendance, enrollment, student)
                )

        rows = filtered_rows

    return [
        {
            "id": attendance.id,
            "enrollment_id": attendance.enrollment_id,
            "student_id": student.id,
            "student_code": student.student_id,
            "student_name": " ".join(
                part for part in
                [student.first_name, student.middle_name, student.last_name]
                if part
            ),
            "class_id": enrollment.class_id,
            "academic_year_id": enrollment.academic_year_id,
            "school_id": enrollment.school_id,
            "attendance_date": attendance.attendance_date,
            "status": attendance.status,
            "remarks": attendance.remarks,
            "marked_by": attendance.marked_by,
        }
        for attendance, enrollment, student in rows
    ]


def request_correction(
    db: Session,
    *,
    actor: User,
    attendance_id: UUID,
    requested_status: str,
    requested_remarks: str | None,
    reason: str,
) -> AttendanceCorrection:
    attendance = db.scalar(
        select(Attendance).where(Attendance.id == attendance_id)
    )

    if attendance is None:
        raise LookupError("Attendance record not found.")

    enrollment = db.scalar(
        select(Enrollment).where(Enrollment.id == attendance.enrollment_id)
    )

    if enrollment is None:
        raise LookupError("Attendance enrollment not found.")

    _validate_scope(
        db,
        actor=actor,
        school_id=enrollment.school_id,
    )

    requested_status = requested_status.upper()

    if requested_status not in STATUS_VALUES:
        raise ValueError("Invalid requested attendance status.")

    if requested_status == attendance.status and requested_remarks == attendance.remarks:
        raise ValueError("Correction does not change the attendance record.")

    pending = db.scalar(
        select(AttendanceCorrection).where(
            AttendanceCorrection.attendance_id == attendance.id,
            AttendanceCorrection.status == CORRECTION_PENDING,
        )
    )

    if pending:
        raise ValueError("A correction request is already pending.")

    correction = AttendanceCorrection(
        attendance_id=attendance.id,
        school_id=enrollment.school_id,
        attendance_date=attendance.attendance_date,
        old_status=attendance.status,
        old_remarks=attendance.remarks,
        requested_status=requested_status,
        requested_remarks=requested_remarks,
        reason=reason,
        status=CORRECTION_PENDING,
        requested_by=actor.id,
    )

    db.add(correction)
    db.flush()

    _audit(
        db,
        actor_user_id=actor.id,
        action="ATTENDANCE_CORRECTION_REQUESTED",
        entity_type="ATTENDANCE_CORRECTION",
        entity_id=correction.id,
        school_id=enrollment.school_id,
        new_values={
            "attendance_id": str(attendance.id),
            "old_status": attendance.status,
            "requested_status": requested_status,
            "reason": reason,
        },
    )

    db.commit()
    db.refresh(correction)

    return correction


def list_corrections(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    status: str | None = None,
) -> list[AttendanceCorrection]:
    _validate_scope(db, actor=actor, school_id=school_id)

    statement = select(AttendanceCorrection).where(
        AttendanceCorrection.school_id == school_id
    )

    if status:
        statement = statement.where(
            AttendanceCorrection.status == status.upper()
        )

    statement = statement.order_by(
        AttendanceCorrection.created_at.desc()
    )

    return list(db.scalars(statement).all())


def approve_correction(
    db: Session,
    *,
    actor: User,
    correction_id: UUID,
    review_remarks: str | None,
) -> AttendanceCorrection:
    correction = db.scalar(
        select(AttendanceCorrection).where(
            AttendanceCorrection.id == correction_id
        )
    )

    if correction is None:
        raise LookupError("Attendance correction request not found.")

    _validate_correction_reviewer(
        db,
        actor=actor,
        requested_by=correction.requested_by,
        school_id=correction.school_id,
    )

    if correction.status != CORRECTION_PENDING:
        raise ValueError("Only pending correction requests can be approved.")

    attendance = db.scalar(
        select(Attendance).where(
            Attendance.id == correction.attendance_id
        )
    )

    if attendance is None:
        raise LookupError("Original attendance record no longer exists.")

    # Prevent approving a stale request after another change.
    if (
        attendance.status != correction.old_status
        or attendance.remarks != correction.old_remarks
    ):
        raise ValueError(
            "Correction request is stale because the attendance record changed."
        )

    old_status = attendance.status
    old_remarks = attendance.remarks

    attendance.status = correction.requested_status
    attendance.remarks = correction.requested_remarks

    correction.status = CORRECTION_APPROVED
    correction.reviewed_by = actor.id
    correction.reviewed_at = datetime.now(timezone.utc)
    correction.review_remarks = review_remarks

    _audit(
        db,
        actor_user_id=actor.id,
        action="ATTENDANCE_CORRECTION_APPROVED",
        entity_type="ATTENDANCE",
        entity_id=attendance.id,
        school_id=correction.school_id,
        old_values={
            "status": old_status,
            "remarks": old_remarks,
        },
        new_values={
            "status": attendance.status,
            "remarks": attendance.remarks,
            "correction_id": str(correction.id),
        },
    )

    db.commit()
    db.refresh(correction)

    return correction


def reject_correction(
    db: Session,
    *,
    actor: User,
    correction_id: UUID,
    review_remarks: str | None,
) -> AttendanceCorrection:
    correction = db.scalar(
        select(AttendanceCorrection).where(
            AttendanceCorrection.id == correction_id
        )
    )

    if correction is None:
        raise LookupError("Attendance correction request not found.")

    _validate_correction_reviewer(
        db,
        actor=actor,
        requested_by=correction.requested_by,
        school_id=correction.school_id,
    )

    if correction.status != CORRECTION_PENDING:
        raise ValueError("Only pending correction requests can be rejected.")

    correction.status = CORRECTION_REJECTED
    correction.reviewed_by = actor.id
    correction.reviewed_at = datetime.now(timezone.utc)
    correction.review_remarks = review_remarks

    _audit(
        db,
        actor_user_id=actor.id,
        action="ATTENDANCE_CORRECTION_REJECTED",
        entity_type="ATTENDANCE_CORRECTION",
        entity_id=correction.id,
        school_id=correction.school_id,
        new_values={
            "status": CORRECTION_REJECTED,
            "review_remarks": review_remarks,
        },
    )

    db.commit()
    db.refresh(correction)

    return correction


def _period_bounds(
    year: AcademicYear,
    *,
    month: int | None = None,
    year_number: int | None = None,
) -> tuple[date, date]:
    if month is not None and year_number is not None:
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")

        start = date(year_number, month, 1)
        end = date(
            year_number,
            month,
            monthrange(year_number, month)[1],
        )

        start = max(start, year.start_date)
        end = min(end, year.end_date)

        return start, end

    return year.start_date, year.end_date


def _working_days(
    db: Session,
    *,
    school_id: UUID,
    academic_year_id: UUID,
    start_date: date,
    end_date: date,
) -> int:
    calendar_rows = list(
        db.scalars(
            select(SchoolCalendar).where(
                SchoolCalendar.school_id == school_id,
                SchoolCalendar.academic_year_id == academic_year_id,
                SchoolCalendar.calendar_date >= start_date,
                SchoolCalendar.calendar_date <= end_date,
            )
        ).all()
    )

    overrides = {
        row.calendar_date: row.is_working_day
        for row in calendar_rows
    }

    total = 0
    current = start_date

    while current <= end_date:
        default_working_day = current.weekday() < 5

        if overrides.get(current, default_working_day):
            total += 1

        current = date.fromordinal(current.toordinal() + 1)

    return total


def _merge_date_ranges(
    ranges: list[tuple[date, date]],
) -> list[tuple[date, date]]:
    if not ranges:
        return []

    ordered = sorted(ranges, key=lambda item: item[0])
    merged = [ordered[0]]

    for start, end in ordered[1:]:
        previous_start, previous_end = merged[-1]

        if start <= date.fromordinal(previous_end.toordinal() + 1):
            merged[-1] = (
                previous_start,
                max(previous_end, end),
            )
        else:
            merged.append((start, end))

    return merged


def _student_report(
    db: Session,
    *,
    enrollments: list[Enrollment],
    student: Student,
    start_date: date,
    end_date: date,
) -> dict:
    relevant_ranges: list[tuple[date, date]] = []

    for enrollment in enrollments:
        enrollment_start = max(
            start_date,
            enrollment.enrollment_date,
        )

        enrollment_end = min(
            end_date,
            enrollment.exit_date or end_date,
        )

        if enrollment_start <= enrollment_end:
            relevant_ranges.append(
                (enrollment_start, enrollment_end)
            )

    merged_ranges = _merge_date_ranges(relevant_ranges)

    working_days = 0

    for range_start, range_end in merged_ranges:
        working_days += _working_days(
            db,
            school_id=enrollments[0].school_id,
            academic_year_id=enrollments[0].academic_year_id,
            start_date=range_start,
            end_date=range_end,
        )

    enrollment_ids = [enrollment.id for enrollment in enrollments]

    records = []

    if enrollment_ids:
        records = list(
            db.scalars(
                select(Attendance).where(
                    Attendance.enrollment_id.in_(enrollment_ids),
                    Attendance.attendance_date >= start_date,
                    Attendance.attendance_date <= end_date,
                )
            ).all()
        )

    counts = {
        "PRESENT": 0,
        "ABSENT": 0,
        "LATE": 0,
        "EXCUSED": 0,
    }

    for record in records:
        if record.status in counts:
            counts[record.status] += 1

    percentage = (
        round((counts["PRESENT"] / working_days) * 100, 2)
        if working_days
        else 0.0
    )

    return {
        "student_id": student.id,
        "student_code": student.student_id,
        "student_name": " ".join(
            part
            for part in [
                student.first_name,
                student.middle_name,
                student.last_name,
            ]
            if part
        ),
        "school_id": enrollments[0].school_id,
        "academic_year_id": enrollments[0].academic_year_id,
        "working_days": working_days,
        "recorded_days": len(records),
        "present_days": counts["PRESENT"],
        "absent_days": counts["ABSENT"],
        "late_days": counts["LATE"],
        "excused_days": counts["EXCUSED"],
        "attendance_percentage": percentage,
    }

def _validate_teacher_report_scope(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID | None,
    start_date: date,
    end_date: date,
) -> None:
    role_name = _role_name(db, actor)

    if role_name != "TEACHER":
        return

    if class_id is None:
        raise PermissionError(
            "Teachers must request attendance reports for an assigned class."
        )

    teacher = db.scalar(
        select(Teacher).where(
            Teacher.user_id == actor.id,
            Teacher.school_id == school_id,
            Teacher.is_active.is_(True),
        )
    )

    if teacher is None:
        raise PermissionError(
            "Teacher is not active in the requested school."
        )

    assignment = db.scalar(
        select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.school_id == school_id,
            TeacherAssignment.academic_year_id == academic_year_id,
            TeacherAssignment.status == "ACTIVE",
            (
                (TeacherAssignment.class_id == class_id)
                | TeacherAssignment.class_id.is_(None)
            ),
            TeacherAssignment.start_date <= end_date,
            (
                (TeacherAssignment.end_date.is_(None))
                | (TeacherAssignment.end_date >= start_date)
            ),
        )
    )

    if assignment is None:
        raise PermissionError(
            "Teacher is not assigned to the requested class for the report period."
        )

def monthly_report(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    month: int,
    year_number: int,
    class_id: UUID | None = None,
    student_id: UUID | None = None,
) -> list[dict]:
    _validate_scope(db, actor=actor, school_id=school_id)

    year = _academic_year(db, academic_year_id)

    start_date, end_date = _period_bounds(
        year,
        month=month,
        year_number=year_number,
    )

    if end_date < start_date:
        return []

    _validate_teacher_report_scope(
        db,
        actor=actor,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        start_date=start_date,
        end_date=end_date,
    )

    statement = (
        select(Enrollment, Student)
        .join(Student, Student.id == Enrollment.student_id)
        .where(
            Enrollment.school_id == school_id,
            Enrollment.academic_year_id == academic_year_id,
            Enrollment.enrollment_date <= end_date,
            (
                (Enrollment.exit_date.is_(None))
                | (Enrollment.exit_date >= start_date)
            ),
        )
    )

    if class_id:
        statement = statement.where(
            Enrollment.class_id == class_id
        )

    if student_id:
        statement = statement.where(
            Enrollment.student_id == student_id
        )

    statement = statement.order_by(
        Enrollment.student_id,
        Enrollment.enrollment_date,
    )

    rows = db.execute(statement).all()

    grouped: dict[UUID, tuple[Student, list[Enrollment]]] = {}

    for enrollment, student in rows:
        if enrollment.student_id not in grouped:
            grouped[enrollment.student_id] = (
                student,
                [],
            )

        grouped[enrollment.student_id][1].append(enrollment)

    result = []

    for student, enrollments in grouped.values():
        report = _student_report(
            db,
            enrollments=enrollments,
            student=student,
            start_date=start_date,
            end_date=end_date,
        )

        report["month"] = month
        report["year"] = year_number

        result.append(report)

    return result

def yearly_report(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID | None = None,
    student_id: UUID | None = None,
) -> list[dict]:
    _validate_scope(db, actor=actor, school_id=school_id)

    year = _academic_year(db, academic_year_id)

    _validate_teacher_report_scope(
        db,
        actor=actor,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        start_date=year.start_date,
        end_date=year.end_date,
    )

    statement = (
        select(Enrollment, Student)
        .join(Student, Student.id == Enrollment.student_id)
        .where(
            Enrollment.school_id == school_id,
            Enrollment.academic_year_id == academic_year_id,
            Enrollment.enrollment_date <= year.end_date,
            (
                (Enrollment.exit_date.is_(None))
                | (Enrollment.exit_date >= year.start_date)
            ),
        )
    )

    if class_id:
        statement = statement.where(
            Enrollment.class_id == class_id
        )

    if student_id:
        statement = statement.where(
            Enrollment.student_id == student_id
        )

    statement = statement.order_by(
        Enrollment.student_id,
        Enrollment.enrollment_date,
    )

    rows = db.execute(statement).all()

    grouped: dict[UUID, tuple[Student, list[Enrollment]]] = {}

    for enrollment, student in rows:
        if enrollment.student_id not in grouped:
            grouped[enrollment.student_id] = (
                student,
                [],
            )

        grouped[enrollment.student_id][1].append(enrollment)

    result = []

    for student, enrollments in grouped.values():
        result.append(
            _student_report(
                db,
                enrollments=enrollments,
                student=student,
                start_date=year.start_date,
                end_date=year.end_date,
            )
        )

    return result

def create_calendar(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    calendar_date: date,
    is_working_day: bool,
    day_type: str,
    holiday_name: str | None,
    remarks: str | None,
) -> SchoolCalendar:
    _validate_scope(db, actor=actor, school_id=school_id)

    year = _academic_year(db, academic_year_id)

    _validate_date_in_year(year, calendar_date)

    existing = _calendar_record(
        db,
        school_id=school_id,
        academic_year_id=academic_year_id,
        attendance_date=calendar_date,
    )

    if existing:
        raise ValueError("A calendar entry already exists for this date.")

    record = SchoolCalendar(
        school_id=school_id,
        academic_year_id=academic_year_id,
        calendar_date=calendar_date,
        is_working_day=is_working_day,
        day_type=day_type,
        holiday_name=holiday_name,
        remarks=remarks,
    )

    db.add(record)
    db.flush()

    _audit(
        db,
        actor_user_id=actor.id,
        action="SCHOOL_CALENDAR_CREATED",
        entity_type="SCHOOL_CALENDAR",
        entity_id=record.id,
        school_id=school_id,
        new_values={
            "calendar_date": str(calendar_date),
            "is_working_day": is_working_day,
            "day_type": day_type,
        },
    )

    db.commit()
    db.refresh(record)

    return record


def update_calendar(
    db: Session,
    *,
    actor: User,
    calendar_id: UUID,
    values: dict,
) -> SchoolCalendar:
    record = db.scalar(
        select(SchoolCalendar).where(
            SchoolCalendar.id == calendar_id
        )
    )

    if record is None:
        raise LookupError("Calendar entry not found.")

    _validate_scope(
        db,
        actor=actor,
        school_id=record.school_id,
    )

    old_values = {
        field: getattr(record, field)
        for field in values
        if hasattr(record, field)
    }

    for field, value in values.items():
        if hasattr(record, field) and value is not None:
            setattr(record, field, value)

    _audit(
        db,
        actor_user_id=actor.id,
        action="SCHOOL_CALENDAR_UPDATED",
        entity_type="SCHOOL_CALENDAR",
        entity_id=record.id,
        school_id=record.school_id,
        old_values=old_values,
        new_values=values,
    )

    db.commit()
    db.refresh(record)

    return record


def list_calendar(
    db: Session,
    *,
    actor: User,
    school_id: UUID,
    academic_year_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[SchoolCalendar]:
    _validate_scope(db, actor=actor, school_id=school_id)

    statement = select(SchoolCalendar).where(
        SchoolCalendar.school_id == school_id,
        SchoolCalendar.academic_year_id == academic_year_id,
    )

    if start_date:
        statement = statement.where(
            SchoolCalendar.calendar_date >= start_date
        )

    if end_date:
        statement = statement.where(
            SchoolCalendar.calendar_date <= end_date
        )

    statement = statement.order_by(SchoolCalendar.calendar_date)

    return list(db.scalars(statement).all())
