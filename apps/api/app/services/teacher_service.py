from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.audit_log import AuditLog
from app.models.class_model import Class
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment
from app.models.teacher_attendance import TeacherAttendance


STATUS_DRAFT = "APPLICATION_DRAFT"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_READY = "READY_FOR_APPROVAL"
STATUS_ACTIVE = "ACTIVE"
STATUS_INACTIVE = "INACTIVE"

ASSIGNMENT_ACTIVE = "ACTIVE"
ASSIGNMENT_INACTIVE = "INACTIVE"

ATTENDANCE_STATUSES = {"PRESENT", "ABSENT", "LEAVE", "HALF_DAY"}


def _audit(
    db,
    *,
    actor_user_id,
    action,
    entity_type,
    entity_id,
    school_id=None,
    old_values=None,
    new_values=None,
):
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            school_id=school_id,
            old_values=old_values,
            new_values=new_values,
            occurred_at=datetime.now(timezone.utc),
        )
    )


def get_by_id(db: Session, teacher_id: UUID) -> Teacher | None:
    return db.scalar(
        select(Teacher).where(Teacher.id == teacher_id)
    )


def list_teachers(
    db: Session,
    *,
    trust_id=None,
    school_id=None,
    include_inactive=False,
):
    stmt = select(Teacher)

    if school_id is not None:
        stmt = stmt.where(Teacher.school_id == school_id)

    elif trust_id is not None:
        stmt = (
            stmt.join(School, School.id == Teacher.school_id)
            .where(School.trust_id == trust_id)
        )

    if not include_inactive:
        stmt = stmt.where(Teacher.is_active.is_(True))

    return list(
        db.scalars(
            stmt.order_by(
                Teacher.first_name.asc(),
                Teacher.last_name.asc(),
            )
        ).all()
    )


def create(db: Session, *, actor_user_id, values):
    values = dict(values)

    school_id = values["school_id"]

    school = db.scalar(
        select(School).where(School.id == school_id)
    )

    if school is None:
        raise LookupError("School not found.")

    if not school.is_active:
        raise ValueError("School is inactive.")

    teacher_id = values["teacher_id"].strip()

    if db.scalar(
        select(Teacher).where(
            Teacher.teacher_id == teacher_id
        )
    ):
        raise ValueError(
            "A teacher with this teacher_id already exists."
        )

    teacher = Teacher(
        **values,
        teacher_id=teacher_id,
        status=STATUS_DRAFT,
        is_active=False,
    )

    db.add(teacher)
    db.flush()

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_CREATED",
        entity_type="TEACHER",
        entity_id=teacher.id,
        school_id=teacher.school_id,
        new_values={
            "teacher_id": teacher.teacher_id,
            "school_id": str(teacher.school_id),
            "status": teacher.status,
        },
    )

    try:
        db.commit()
        db.refresh(teacher)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Unable to create teacher because a unique constraint was violated."
        )

    return teacher


def update(
    db: Session,
    teacher: Teacher,
    *,
    actor_user_id,
    values,
):
    if teacher.status == STATUS_INACTIVE:
        raise ValueError("Inactive teachers cannot be edited.")

    values = dict(values)

    # School ownership is immutable after application creation.
    values.pop("school_id", None)

    old = {
        key: getattr(teacher, key)
        for key in values
        if hasattr(teacher, key)
    }

    for key, value in values.items():
        if hasattr(teacher, key):
            setattr(teacher, key, value)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_UPDATED",
        entity_type="TEACHER",
        entity_id=teacher.id,
        school_id=teacher.school_id,
        old_values=old,
        new_values=values,
    )

    db.commit()
    db.refresh(teacher)

    return teacher


def submit(
    db: Session,
    teacher: Teacher,
    *,
    actor_user_id,
):
    if teacher.status != STATUS_DRAFT:
        raise ValueError(
            "Only application drafts can be submitted."
        )

    old = teacher.status
    teacher.status = STATUS_SUBMITTED

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_SUBMITTED",
        entity_type="TEACHER",
        entity_id=teacher.id,
        school_id=teacher.school_id,
        old_values={"status": old},
        new_values={"status": teacher.status},
    )

    db.commit()
    db.refresh(teacher)

    return teacher


def prepare_for_approval(
    db: Session,
    teacher: Teacher,
    *,
    actor_user_id,
):
    if teacher.status != STATUS_SUBMITTED:
        raise ValueError(
            "Only submitted teacher applications can enter approval."
        )

    old = teacher.status
    teacher.status = STATUS_READY

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_READY_FOR_APPROVAL",
        entity_type="TEACHER",
        entity_id=teacher.id,
        school_id=teacher.school_id,
        old_values={"status": old},
        new_values={"status": teacher.status},
    )

    db.commit()
    db.refresh(teacher)

    return teacher


def approve(
    db: Session,
    teacher: Teacher,
    *,
    actor_user_id,
):
    if teacher.status != STATUS_READY:
        raise ValueError(
            "Only teacher applications ready for approval can be approved."
        )

    old = {
        "status": teacher.status,
        "is_active": teacher.is_active,
    }

    teacher.status = STATUS_ACTIVE
    teacher.is_active = True

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_APPROVED",
        entity_type="TEACHER",
        entity_id=teacher.id,
        school_id=teacher.school_id,
        old_values=old,
        new_values={
            "status": teacher.status,
            "is_active": teacher.is_active,
        },
    )

    db.commit()
    db.refresh(teacher)

    return teacher


def deactivate(
    db: Session,
    teacher: Teacher,
    *,
    actor_user_id,
):
    if teacher.status != STATUS_ACTIVE or not teacher.is_active:
        raise ValueError(
            "Only active teachers can be deactivated."
        )

    old = {
        "status": teacher.status,
        "is_active": teacher.is_active,
    }

    teacher.status = STATUS_INACTIVE
    teacher.is_active = False

    db.execute(
        update(TeacherAssignment)
        .where(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.status == ASSIGNMENT_ACTIVE,
        )
        .values(status=ASSIGNMENT_INACTIVE)
    )

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_DEACTIVATED",
        entity_type="TEACHER",
        entity_id=teacher.id,
        school_id=teacher.school_id,
        old_values=old,
        new_values={
            "status": teacher.status,
            "is_active": teacher.is_active,
        },
    )

    db.commit()
    db.refresh(teacher)

    return teacher


def _validate_assignment_target(
    db: Session,
    *,
    teacher_id,
    school_id,
    academic_year_id,
    class_id,
    start_date,
    end_date,
):
    teacher = get_by_id(db, teacher_id)

    if teacher is None:
        raise LookupError("Teacher not found.")

    if teacher.school_id != school_id:
        raise ValueError(
            "Teacher does not belong to the selected school."
        )

    if not teacher.is_active or teacher.status != STATUS_ACTIVE:
        raise ValueError(
            "Only active teachers can be assigned."
        )

    school = db.scalar(
        select(School).where(School.id == school_id)
    )

    if school is None:
        raise LookupError("School not found.")

    if not school.is_active:
        raise ValueError("School is inactive.")

    year = db.scalar(
        select(AcademicYear).where(
            AcademicYear.id == academic_year_id
        )
    )

    if year is None:
        raise LookupError("Academic year not found.")

    if not year.is_active:
        raise ValueError("Academic year is inactive.")

    if school.trust_id != year.trust_id:
        raise ValueError(
            "School and academic year belong to different trusts."
        )

    attached = db.scalar(
        select(SchoolAcademicYear).where(
            SchoolAcademicYear.school_id == school_id,
            SchoolAcademicYear.academic_year_id == academic_year_id,
        )
    )

    if attached is None:
        raise ValueError(
            "School is not attached to this academic year."
        )

    if start_date < year.start_date or start_date > year.end_date:
        raise ValueError(
            "Assignment start date must fall within the academic year."
        )

    if end_date is not None and (
        end_date < start_date
        or end_date > year.end_date
    ):
        raise ValueError(
            "Assignment end date must fall within the academic year."
        )

    if class_id is not None:
        cls = db.scalar(
            select(Class).where(Class.id == class_id)
        )

        if cls is None:
            raise LookupError("Class not found.")

        if not cls.is_active:
            raise ValueError("Class is inactive.")

        if (
            cls.school_id != school_id
            or cls.academic_year_id != academic_year_id
        ):
            raise ValueError(
                "Class does not belong to the selected school and academic year."
            )

    return teacher, school


def _assignment_overlap_condition(
    start_date,
    end_date,
):
    # Existing assignment overlaps the new interval when:
    #
    # existing.start <= new.end
    # AND
    # existing.end >= new.start
    #
    # An open-ended interval has no upper boundary.

    if end_date is None:
        return or_(
            TeacherAssignment.end_date.is_(None),
            TeacherAssignment.end_date >= start_date,
        )

    return and_(
        TeacherAssignment.start_date <= end_date,
        or_(
            TeacherAssignment.end_date.is_(None),
            TeacherAssignment.end_date >= start_date,
        ),
    )


def create_assignment(
    db: Session,
    *,
    actor_user_id,
    **values,
):
    teacher, school = _validate_assignment_target(
        db,
        **values,
    )

    stmt = select(TeacherAssignment).where(
        TeacherAssignment.teacher_id == values["teacher_id"],
        TeacherAssignment.school_id == values["school_id"],
        TeacherAssignment.academic_year_id == values["academic_year_id"],
        TeacherAssignment.status == ASSIGNMENT_ACTIVE,
        (
            TeacherAssignment.class_id.is_(None)
            if values["class_id"] is None
            else TeacherAssignment.class_id == values["class_id"]
        ),
        (
            TeacherAssignment.subject.is_(None)
            if values["subject"] is None
            else TeacherAssignment.subject == values["subject"]
        ),
        _assignment_overlap_condition(
            values["start_date"],
            values["end_date"],
        ),
    )

    if db.scalar(stmt):
        raise ValueError(
            "An overlapping active assignment already exists for this teacher, class and subject."
        )

    assignment = TeacherAssignment(
        **values,
        status=ASSIGNMENT_ACTIVE,
    )

    db.add(assignment)
    db.flush()

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_ASSIGNED",
        entity_type="TEACHER_ASSIGNMENT",
        entity_id=assignment.id,
        school_id=school.id,
        new_values={
            "teacher_id": str(teacher.id),
            "school_id": str(school.id),
            "class_id": (
                str(assignment.class_id)
                if assignment.class_id
                else None
            ),
            "subject": assignment.subject,
        },
    )

    try:
        db.commit()
        db.refresh(assignment)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Unable to create teacher assignment."
        )

    return assignment


def get_assignment(db: Session, assignment_id):
    return db.scalar(
        select(TeacherAssignment).where(
            TeacherAssignment.id == assignment_id
        )
    )


def list_assignments(
    db: Session,
    *,
    teacher_id=None,
    school_id=None,
    academic_year_id=None,
    include_inactive=False,
):
    stmt = select(TeacherAssignment)

    if teacher_id is not None:
        stmt = stmt.where(
            TeacherAssignment.teacher_id == teacher_id
        )

    if school_id is not None:
        stmt = stmt.where(
            TeacherAssignment.school_id == school_id
        )

    if academic_year_id is not None:
        stmt = stmt.where(
            TeacherAssignment.academic_year_id == academic_year_id
        )

    if not include_inactive:
        stmt = stmt.where(
            TeacherAssignment.status == ASSIGNMENT_ACTIVE
        )

    return list(
        db.scalars(
            stmt.order_by(
                TeacherAssignment.start_date.desc()
            )
        ).all()
    )


def update_assignment(
    db: Session,
    assignment: TeacherAssignment,
    *,
    actor_user_id,
    values,
):
    values = dict(values)

    candidate = {
        "teacher_id": assignment.teacher_id,
        "school_id": assignment.school_id,
        "academic_year_id": assignment.academic_year_id,
        "class_id": values.get(
            "class_id",
            assignment.class_id,
        ),
        "subject": values.get(
            "subject",
            assignment.subject,
        ),
        "start_date": values.get(
            "start_date",
            assignment.start_date,
        ),
        "end_date": values.get(
            "end_date",
            assignment.end_date,
        ),
    }

    if (
        candidate["end_date"] is not None
        and candidate["end_date"] < candidate["start_date"]
    ):
        raise ValueError(
            "end_date cannot be before start_date."
        )

    _validate_assignment_target(
        db,
        **candidate,
    )

    overlap_stmt = select(TeacherAssignment).where(
        TeacherAssignment.id != assignment.id,
        TeacherAssignment.teacher_id == candidate["teacher_id"],
        TeacherAssignment.school_id == candidate["school_id"],
        TeacherAssignment.academic_year_id == candidate["academic_year_id"],
        TeacherAssignment.status == ASSIGNMENT_ACTIVE,
        (
            TeacherAssignment.class_id.is_(None)
            if candidate["class_id"] is None
            else TeacherAssignment.class_id == candidate["class_id"]
        ),
        (
            TeacherAssignment.subject.is_(None)
            if candidate["subject"] is None
            else TeacherAssignment.subject == candidate["subject"]
        ),
        _assignment_overlap_condition(
            candidate["start_date"],
            candidate["end_date"],
        ),
    )

    if db.scalar(overlap_stmt):
        raise ValueError(
            "The updated assignment overlaps another active assignment."
        )

    old = {
        "class_id": (
            str(assignment.class_id)
            if assignment.class_id
            else None
        ),
        "subject": assignment.subject,
        "start_date": str(assignment.start_date),
        "end_date": (
            str(assignment.end_date)
            if assignment.end_date
            else None
        ),
        "status": assignment.status,
    }

    for key, value in values.items():
        if hasattr(assignment, key):
            setattr(assignment, key, value)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_ASSIGNMENT_UPDATED",
        entity_type="TEACHER_ASSIGNMENT",
        entity_id=assignment.id,
        school_id=assignment.school_id,
        old_values=old,
        new_values={
            key: str(value)
            if isinstance(value, UUID)
            else value
            for key, value in values.items()
        },
    )

    db.commit()
    db.refresh(assignment)

    return assignment


def deactivate_assignment(
    db: Session,
    assignment: TeacherAssignment,
    *,
    actor_user_id,
):
    if assignment.status != ASSIGNMENT_ACTIVE:
        raise ValueError(
            "Only active assignments can be deactivated."
        )

    old = {"status": assignment.status}

    assignment.status = ASSIGNMENT_INACTIVE

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="TEACHER_ASSIGNMENT_DEACTIVATED",
        entity_type="TEACHER_ASSIGNMENT",
        entity_id=assignment.id,
        school_id=assignment.school_id,
        old_values=old,
        new_values={"status": assignment.status},
    )

    db.commit()
    db.refresh(assignment)

    return assignment


def has_assignment_on_date(
    db: Session,
    *,
    teacher_id,
    school_id,
    attendance_date,
):
    return db.scalar(
        select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.school_id == school_id,
            TeacherAssignment.status == ASSIGNMENT_ACTIVE,
            TeacherAssignment.start_date <= attendance_date,
            or_(
                TeacherAssignment.end_date.is_(None),
                TeacherAssignment.end_date >= attendance_date,
            ),
        )
    )


def mark_attendance(
    db: Session,
    *,
    teacher_id,
    school_id,
    attendance_date,
    status,
    remarks,
    marked_by,
):
    if status not in ATTENDANCE_STATUSES:
        raise ValueError(
            f"Invalid attendance status. Allowed: {', '.join(sorted(ATTENDANCE_STATUSES))}."
        )

    teacher = get_by_id(db, teacher_id)

    if teacher is None:
        raise LookupError("Teacher not found.")

    if teacher.school_id != school_id:
        raise ValueError(
            "Teacher does not belong to the selected school."
        )

    if not teacher.is_active:
        raise ValueError(
            "Inactive teachers cannot have attendance marked."
        )

    if not has_assignment_on_date(
        db,
        teacher_id=teacher_id,
        school_id=school_id,
        attendance_date=attendance_date,
    ):
        raise ValueError(
            "Teacher has no active assignment at this school on the attendance date."
        )

    existing = db.scalar(
        select(TeacherAttendance).where(
            TeacherAttendance.teacher_id == teacher_id,
            TeacherAttendance.attendance_date == attendance_date,
        )
    )

    if existing:
        raise ValueError(
            "Teacher attendance already exists for this date."
        )

    record = TeacherAttendance(
        teacher_id=teacher_id,
        attendance_date=attendance_date,
        status=status,
        marked_by=marked_by,
        remarks=remarks,
    )

    db.add(record)
    db.flush()

    _audit(
        db,
        actor_user_id=marked_by,
        action="TEACHER_ATTENDANCE_MARKED",
        entity_type="TEACHER_ATTENDANCE",
        entity_id=record.id,
        school_id=school_id,
        new_values={
            "teacher_id": str(teacher_id),
            "date": str(attendance_date),
            "status": status,
        },
    )

    try:
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Teacher attendance already exists for this date."
        )

    return record


def list_attendance(
    db: Session,
    *,
    teacher_id=None,
    school_id=None,
    trust_id=None,
    start_date=None,
    end_date=None,
):
    stmt = select(TeacherAttendance)

    if school_id is not None:
        stmt = stmt.join(
            Teacher,
            Teacher.id == TeacherAttendance.teacher_id,
        ).where(
            Teacher.school_id == school_id
        )

    elif trust_id is not None:
        stmt = (
            stmt.join(
                Teacher,
                Teacher.id == TeacherAttendance.teacher_id,
            )
            .join(
                School,
                School.id == Teacher.school_id,
            )
            .where(
                School.trust_id == trust_id
            )
        )

    if teacher_id is not None:
        stmt = stmt.where(
            TeacherAttendance.teacher_id == teacher_id
        )

    if start_date is not None:
        stmt = stmt.where(
            TeacherAttendance.attendance_date >= start_date
        )

    if end_date is not None:
        stmt = stmt.where(
            TeacherAttendance.attendance_date <= end_date
        )

    return list(
        db.scalars(
            stmt.order_by(
                TeacherAttendance.attendance_date.desc()
            )
        ).all()
    )
