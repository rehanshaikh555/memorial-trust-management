from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import and_, exists, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.audit_log import AuditLog
from app.models.class_model import Class
from app.models.document_verification import DocumentVerification
from app.models.enrollment import Enrollment
from app.models.guardian import Guardian
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear
from app.models.student import Student
from app.models.student_document import StudentDocument
from app.models.student_guardian import StudentGuardian


STATUS_DRAFT = "APPLICATION_DRAFT"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_READY = "READY_FOR_APPROVAL"
STATUS_ACTIVE = "ACTIVE"
STATUS_TRANSFERRED = "TRANSFERRED"
STATUS_LEFT = "LEFT"
STATUS_GRADUATED = "GRADUATED"
STATUS_ARCHIVED = "ARCHIVED"

ENROLLMENT_ACTIVE = "ACTIVE"
ENROLLMENT_TRANSFERRED = "TRANSFERRED"
ENROLLMENT_LEFT = "LEFT"
ENROLLMENT_GRADUATED = "GRADUATED"


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


def get_by_id(db: Session, student_pk: UUID) -> Student | None:
    return db.scalar(select(Student).where(Student.id == student_pk))


def require_by_id(db: Session, student_pk: UUID) -> Student:
    student = get_by_id(db, student_pk)
    if student is None:
        raise LookupError("Student not found.")
    return student


def get_current_enrollment(db: Session, student_pk: UUID) -> Enrollment | None:
    return db.scalar(
        select(Enrollment)
        .where(
            Enrollment.student_id == student_pk,
            Enrollment.status == ENROLLMENT_ACTIVE,
        )
        .order_by(Enrollment.enrollment_date.desc())
    )


def get_current_school_id(db: Session, student_pk: UUID) -> UUID | None:
    enrollment = get_current_enrollment(db, student_pk)
    return enrollment.school_id if enrollment else None


def list_students(
    db: Session,
    *,
    trust_id: UUID | None = None,
    school_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    class_id: UUID | None = None,
    status: str | None = None,
    include_inactive: bool = False,
) -> list[tuple[Student, Enrollment | None]]:
    current_enrollment = (
        select(Enrollment)
        .where(
            Enrollment.student_id == Student.id,
            Enrollment.status == ENROLLMENT_ACTIVE,
        )
        .order_by(Enrollment.enrollment_date.desc())
        .limit(1)
        .lateral()
    )

    statement = (
        select(Student, current_enrollment)
        .join(current_enrollment, True, isouter=True)
        .join(School, School.id == current_enrollment.c.school_id, isouter=True)
    )

    if trust_id is not None:
        statement = statement.where(School.trust_id == trust_id)

    if school_id is not None:
        statement = statement.where(current_enrollment.c.school_id == school_id)

    if academic_year_id is not None:
        statement = statement.where(
            current_enrollment.c.academic_year_id == academic_year_id
        )

    if class_id is not None:
        statement = statement.where(current_enrollment.c.class_id == class_id)

    if status is not None:
        statement = statement.where(Student.status == status)

    if not include_inactive:
        statement = statement.where(Student.is_active.is_(True))

    statement = statement.order_by(Student.last_name, Student.first_name)

    return list(db.execute(statement).all())


def _validate_enrollment_target(
    db: Session,
    *,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    enrollment_date: date,
) -> tuple[School, AcademicYear, Class]:
    school = db.scalar(select(School).where(School.id == school_id))
    if school is None:
        raise LookupError("School not found.")
    if not school.is_active:
        raise ValueError("School is inactive.")

    academic_year = db.scalar(
        select(AcademicYear).where(AcademicYear.id == academic_year_id)
    )
    if academic_year is None:
        raise LookupError("Academic year not found.")
    if not academic_year.is_active:
        raise ValueError("Academic year is inactive.")

    if school.trust_id != academic_year.trust_id:
        raise PermissionError("School does not belong to the academic year's trust.")

    attached = db.scalar(
        select(SchoolAcademicYear).where(
            SchoolAcademicYear.school_id == school_id,
            SchoolAcademicYear.academic_year_id == academic_year_id,
        )
    )
    if attached is None:
        raise ValueError("School is not attached to this academic year.")

    class_record = db.scalar(select(Class).where(Class.id == class_id))
    if class_record is None:
        raise LookupError("Class not found.")
    if not class_record.is_active:
        raise ValueError("Class is inactive.")

    if (
        class_record.school_id != school_id
        or class_record.academic_year_id != academic_year_id
    ):
        raise ValueError("Class does not belong to the selected school and academic year.")

    if enrollment_date < academic_year.start_date or enrollment_date > academic_year.end_date:
        raise ValueError("Enrollment date must fall within the academic year.")

    return school, academic_year, class_record


def create(
    db: Session,
    *,
    actor_user_id: UUID,
    student_id: str,
    first_name: str,
    middle_name: str | None,
    last_name: str,
    date_of_birth: date,
    gender: str | None,
    phone: str | None,
    email: str | None,
    address: str | None,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    enrollment_date: date,
    guardians: list[dict],
) -> Student:
    _validate_enrollment_target(
        db,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        enrollment_date=enrollment_date,
    )

    existing = db.scalar(
        select(Student).where(Student.student_id == student_id)
    )
    if existing is not None:
        raise ValueError("A student with this student_id already exists.")

    student = Student(
        student_id=student_id,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        phone=phone,
        email=email,
        address=address,
        status=STATUS_DRAFT,
        is_active=False,
    )
    db.add(student)
    db.flush()

    enrollment = Enrollment(
        student_id=student.id,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        enrollment_date=enrollment_date,
        status=ENROLLMENT_ACTIVE,
    )
    db.add(enrollment)

    primary_count = 0
    for data in guardians:
        guardian = Guardian(
            full_name=data["full_name"],
            relationship=data["relationship"],
            phone=data["phone"],
            email=data.get("email"),
            address=data.get("address"),
        )
        db.add(guardian)
        db.flush()

        is_primary = bool(data.get("is_primary", False))
        primary_count += int(is_primary)

        db.add(
            StudentGuardian(
                student_id=student.id,
                guardian_id=guardian.id,
                is_primary=is_primary,
            )
        )

    if primary_count > 1:
        db.rollback()
        raise ValueError("A student can have only one primary guardian.")

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_CREATED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=school_id,
        new_values={"student_id": student.student_id, "status": student.status},
    )

    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise ValueError("Unable to create student because a unique constraint was violated.")

    return student


def update(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
    values: dict,
) -> Student:
    if student.status in {STATUS_ARCHIVED, STATUS_GRADUATED}:
        raise ValueError("This student can no longer be edited.")

    old_values = {
        field: getattr(student, field)
        for field in values
        if hasattr(student, field)
    }

    for field, value in values.items():
        if hasattr(student, field):
            setattr(student, field, value)

    school_id = get_current_school_id(db, student.id)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_UPDATED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=school_id,
        old_values=old_values,
        new_values=values,
    )

    db.commit()
    db.refresh(student)
    return student


def submit(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
) -> Student:
    if student.status != STATUS_DRAFT:
        raise ValueError("Only application drafts can be submitted.")

    student.status = STATUS_SUBMITTED
    school_id = get_current_school_id(db, student.id)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_SUBMITTED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=school_id,
        old_values={"status": STATUS_DRAFT},
        new_values={"status": STATUS_SUBMITTED},
    )

    db.commit()
    db.refresh(student)
    return student


def prepare_for_approval(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
) -> Student:
    if student.status != STATUS_SUBMITTED:
        raise ValueError("Only submitted applications can enter approval.")

    documents = list(
        db.scalars(
            select(StudentDocument).where(
                StudentDocument.student_id == student.id
            )
        ).all()
    )

    if not documents:
        raise ValueError("At least one student document is required before approval.")

    if any(document.status != "VERIFIED" for document in documents):
        raise ValueError("All uploaded student documents must be verified.")

    student.status = STATUS_READY

    school_id = get_current_school_id(db, student.id)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_READY_FOR_APPROVAL",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=school_id,
        old_values={"status": STATUS_SUBMITTED},
        new_values={"status": STATUS_READY},
    )

    db.commit()
    db.refresh(student)
    return student


def approve(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
) -> Student:
    if student.status not in {STATUS_SUBMITTED, STATUS_READY}:
        raise ValueError("Only submitted or ready applications can be approved.")

    documents = list(
        db.scalars(
            select(StudentDocument).where(
                StudentDocument.student_id == student.id
            )
        ).all()
    )

    if not documents:
        raise ValueError("At least one verified student document is required.")

    if any(document.status != "VERIFIED" for document in documents):
        raise ValueError("All uploaded student documents must be verified.")

    enrollment = get_current_enrollment(db, student.id)
    if enrollment is None:
        raise ValueError("Student has no active enrollment.")

    old_status = student.status
    student.status = STATUS_ACTIVE
    student.is_active = True

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_APPROVED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=enrollment.school_id,
        old_values={"status": old_status, "is_active": False},
        new_values={"status": STATUS_ACTIVE, "is_active": True},
    )

    db.commit()
    db.refresh(student)
    return student


def transfer(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    enrollment_date: date,
) -> Student:
    if student.status != STATUS_ACTIVE or not student.is_active:
        raise ValueError("Only active students can be transferred.")

    target_school, _, _ = _validate_enrollment_target(
        db,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        enrollment_date=enrollment_date,
    )

    current = get_current_enrollment(db, student.id)
    if current is None:
        raise ValueError("Student has no active enrollment.")

    if (
        current.school_id == school_id
        and current.academic_year_id == academic_year_id
        and current.class_id == class_id
    ):
        raise ValueError("Student is already enrolled in the selected class.")

    current.exit_date = enrollment_date
    current.status = ENROLLMENT_TRANSFERRED

    db.add(
        Enrollment(
            student_id=student.id,
            school_id=school_id,
            academic_year_id=academic_year_id,
            class_id=class_id,
            enrollment_date=enrollment_date,
            status=ENROLLMENT_ACTIVE,
        )
    )

    old_school_id = current.school_id
    student.status = STATUS_TRANSFERRED

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_TRANSFERRED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=target_school.id,
        old_values={
            "school_id": str(old_school_id),
            "class_id": str(current.class_id),
            "status": STATUS_ACTIVE,
        },
        new_values={
            "school_id": str(school_id),
            "class_id": str(class_id),
            "status": STATUS_TRANSFERRED,
        },
    )

    # A transfer creates a new active enrollment. The student remains active.
    student.status = STATUS_ACTIVE

    db.commit()
    db.refresh(student)
    return student


def exit_student(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
    exit_date: date,
) -> Student:
    if student.status != STATUS_ACTIVE or not student.is_active:
        raise ValueError("Only active students can exit.")

    enrollment = get_current_enrollment(db, student.id)
    if enrollment is None:
        raise ValueError("Student has no active enrollment.")

    if exit_date < enrollment.enrollment_date:
        raise ValueError("Exit date cannot be before enrollment date.")

    enrollment.exit_date = exit_date
    enrollment.status = ENROLLMENT_LEFT
    student.status = STATUS_LEFT
    student.is_active = False

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_EXITED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=enrollment.school_id,
        new_values={"status": STATUS_LEFT, "is_active": False, "exit_date": str(exit_date)},
    )

    db.commit()
    db.refresh(student)
    return student


def graduate(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
    exit_date: date,
) -> Student:
    if student.status != STATUS_ACTIVE or not student.is_active:
        raise ValueError("Only active students can graduate.")

    enrollment = get_current_enrollment(db, student.id)
    if enrollment is None:
        raise ValueError("Student has no active enrollment.")

    if exit_date < enrollment.enrollment_date:
        raise ValueError("Graduation date cannot be before enrollment date.")

    enrollment.exit_date = exit_date
    enrollment.status = ENROLLMENT_GRADUATED
    student.status = STATUS_GRADUATED
    student.is_active = False

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_GRADUATED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=enrollment.school_id,
        new_values={"status": STATUS_GRADUATED, "is_active": False},
    )

    db.commit()
    db.refresh(student)
    return student


def add_guardian(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
    full_name: str,
    relationship: str,
    phone: str,
    email: str | None,
    address: str | None,
    is_primary: bool,
) -> Guardian:
    if student.status == STATUS_ARCHIVED:
        raise ValueError("Archived students cannot be modified.")

    if is_primary:
        db.execute(
            update(StudentGuardian)
            .where(StudentGuardian.student_id == student.id)
            .values(is_primary=False)
        )

    guardian = Guardian(
        full_name=full_name,
        relationship=relationship,
        phone=phone,
        email=email,
        address=address,
    )
    db.add(guardian)
    db.flush()

    db.add(
        StudentGuardian(
            student_id=student.id,
            guardian_id=guardian.id,
            is_primary=is_primary,
        )
    )

    school_id = get_current_school_id(db, student.id)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_GUARDIAN_ADDED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=school_id,
        new_values={"guardian_id": str(guardian.id), "is_primary": is_primary},
    )

    try:
        db.commit()
        db.refresh(guardian)
    except IntegrityError:
        db.rollback()
        raise ValueError("Unable to add guardian.")

    return guardian


def list_guardians(db: Session, student_pk: UUID) -> list[tuple[Guardian, bool]]:
    statement = (
        select(Guardian, StudentGuardian.is_primary)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(StudentGuardian.student_id == student_pk)
        .order_by(StudentGuardian.is_primary.desc(), Guardian.full_name)
    )
    return list(db.execute(statement).all())


def update_guardian(
    db: Session,
    student: Student,
    guardian: Guardian,
    *,
    actor_user_id: UUID,
    values: dict,
    is_primary: bool | None,
) -> Guardian:
    link = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == guardian.id,
        )
    )
    if link is None:
        raise LookupError("Guardian is not linked to this student.")

    for field, value in values.items():
        if hasattr(guardian, field):
            setattr(guardian, field, value)

    if is_primary is True:
        db.execute(
            update(StudentGuardian)
            .where(StudentGuardian.student_id == student.id)
            .values(is_primary=False)
        )
        link.is_primary = True
    elif is_primary is False:
        link.is_primary = False

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_GUARDIAN_UPDATED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=get_current_school_id(db, student.id),
        new_values={"guardian_id": str(guardian.id), "is_primary": link.is_primary},
    )

    db.commit()
    db.refresh(guardian)
    return guardian


def remove_guardian(
    db: Session,
    student: Student,
    guardian: Guardian,
    *,
    actor_user_id: UUID,
) -> None:
    link = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == guardian.id,
        )
    )
    if link is None:
        raise LookupError("Guardian is not linked to this student.")

    db.delete(link)
    db.flush()

    remaining = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id
        )
    )
    if remaining is None:
        # Guardian relationship is not mandatory at database level, so no issue.
        pass

    db.delete(guardian)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_GUARDIAN_REMOVED",
        entity_type="STUDENT",
        entity_id=student.id,
        school_id=get_current_school_id(db, student.id),
        new_values={"guardian_id": str(guardian.id)},
    )

    db.commit()


def add_document(
    db: Session,
    student: Student,
    *,
    actor_user_id: UUID,
    document_type: str,
    file_name: str,
    storage_path: str,
    mime_type: str,
    file_size: int,
    expiry_date: date | None,
) -> StudentDocument:
    if student.status == STATUS_ARCHIVED:
        raise ValueError("Archived students cannot receive documents.")

    document = StudentDocument(
        student_id=student.id,
        document_type=document_type,
        file_name=file_name,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size=file_size,
        status="PENDING",
        expiry_date=expiry_date,
    )
    db.add(document)
    db.flush()

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_DOCUMENT_UPLOADED",
        entity_type="STUDENT_DOCUMENT",
        entity_id=document.id,
        school_id=get_current_school_id(db, student.id),
        new_values={
            "student_id": str(student.id),
            "document_type": document_type,
            "status": "PENDING",
        },
    )

    db.commit()
    db.refresh(document)
    return document


def list_documents(db: Session, student_pk: UUID) -> list[StudentDocument]:
    return list(
        db.scalars(
            select(StudentDocument)
            .where(StudentDocument.student_id == student_pk)
            .order_by(StudentDocument.created_at.desc())
        ).all()
    )


def verify_document(
    db: Session,
    document: StudentDocument,
    *,
    actor_user_id: UUID,
    remarks: str | None,
) -> StudentDocument:
    if document.status not in {"PENDING", "REJECTED"}:
        raise ValueError("Only pending or rejected documents can be verified.")

    document.status = "VERIFIED"
    document.rejection_reason = None

    db.add(
        DocumentVerification(
            document_id=document.id,
            verified_by=actor_user_id,
            status="VERIFIED",
            remarks=remarks,
            verified_at=datetime.now(timezone.utc),
        )
    )

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_DOCUMENT_VERIFIED",
        entity_type="STUDENT_DOCUMENT",
        entity_id=document.id,
        school_id=get_current_school_id(db, document.student_id),
        new_values={"status": "VERIFIED"},
    )

    db.commit()
    db.refresh(document)
    return document


def reject_document(
    db: Session,
    document: StudentDocument,
    *,
    actor_user_id: UUID,
    reason: str,
) -> StudentDocument:
    if document.status not in {"PENDING", "VERIFIED"}:
        raise ValueError("Only pending or verified documents can be rejected.")

    document.status = "REJECTED"
    document.rejection_reason = reason

    db.add(
        DocumentVerification(
            document_id=document.id,
            verified_by=actor_user_id,
            status="REJECTED",
            remarks=reason,
            verified_at=datetime.now(timezone.utc),
        )
    )

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="STUDENT_DOCUMENT_REJECTED",
        entity_type="STUDENT_DOCUMENT",
        entity_id=document.id,
        school_id=get_current_school_id(db, document.student_id),
        new_values={"status": "REJECTED", "reason": reason},
    )

    db.commit()
    db.refresh(document)
    return document


def get_document(db: Session, document_id: UUID) -> StudentDocument | None:
    return db.scalar(
        select(StudentDocument).where(StudentDocument.id == document_id)
    )