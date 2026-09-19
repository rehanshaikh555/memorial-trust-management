from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.class_model import Class
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear
from app.schemas.class_model import ClassCreate, ClassUpdate


def get_by_id(db: Session, class_id: UUID) -> Class | None:
    return db.scalar(select(Class).where(Class.id == class_id))


def require_by_id(db: Session, class_id: UUID) -> Class:
    class_record = get_by_id(db, class_id)
    if class_record is None:
        raise LookupError("Class not found.")
    return class_record


def list_all(
    db: Session,
    *,
    school_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    include_inactive: bool = False,
) -> list[Class]:
    statement = select(Class)

    if school_id is not None:
        statement = statement.where(Class.school_id == school_id)

    if academic_year_id is not None:
        statement = statement.where(Class.academic_year_id == academic_year_id)

    if not include_inactive:
        statement = statement.where(Class.is_active.is_(True))

    statement = statement.order_by(
        Class.grade_level.asc(),
        Class.section.asc().nullsfirst(),
        Class.name.asc(),
    )

    return list(db.scalars(statement).all())


def _validate_school_and_academic_year(
    db: Session,
    school_id: UUID,
    academic_year_id: UUID,
) -> None:
    school = db.scalar(select(School).where(School.id == school_id))

    if school is None:
        raise LookupError("School not found.")

    if not school.is_active:
        raise ValueError(
            "Cannot create or update a class in an inactive school."
        )

    academic_year = db.scalar(
        select(AcademicYear).where(AcademicYear.id == academic_year_id)
    )

    if academic_year is None:
        raise LookupError("Academic year not found.")

    if not academic_year.is_active:
        raise ValueError(
            "Cannot create or update a class in an inactive academic year."
        )

    if academic_year.trust_id != school.trust_id:
        raise PermissionError(
            "School and academic year do not belong to the same trust."
        )

    association = db.get(
        SchoolAcademicYear,
        (school_id, academic_year_id),
    )

    if association is None:
        raise ValueError(
            "School is not attached to this academic year."
        )


def create(db: Session, data: ClassCreate) -> Class:
    _validate_school_and_academic_year(
        db,
        data.school_id,
        data.academic_year_id,
    )

    existing = db.scalar(
        select(Class).where(
            Class.school_id == data.school_id,
            Class.academic_year_id == data.academic_year_id,
            Class.grade_level == data.grade_level,
            Class.section == data.section,
        )
    )

    if existing is not None:
        raise ValueError(
            "A class with this grade and section already exists."
        )

    class_record = Class(
        school_id=data.school_id,
        academic_year_id=data.academic_year_id,
        name=data.name.strip(),
        grade_level=data.grade_level,
        section=data.section,
        is_active=True,
    )

    db.add(class_record)

    try:
        db.commit()
        db.refresh(class_record)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "A class with this grade and section already exists."
        ) from None

    return class_record


def update(
    db: Session,
    class_record: Class,
    data: ClassUpdate,
) -> Class:
    if not class_record.is_active:
        raise ValueError("Cannot update an inactive class.")

    updates = data.model_dump(exclude_unset=True)

    new_name = (
        updates["name"].strip()
        if "name" in updates and updates["name"] is not None
        else class_record.name
    )

    new_grade = (
        updates["grade_level"]
        if "grade_level" in updates and updates["grade_level"] is not None
        else class_record.grade_level
    )

    new_section = (
        updates["section"]
        if "section" in updates
        else class_record.section
    )

    _validate_school_and_academic_year(
        db,
        class_record.school_id,
        class_record.academic_year_id,
    )

    duplicate = db.scalar(
        select(Class).where(
            Class.school_id == class_record.school_id,
            Class.academic_year_id == class_record.academic_year_id,
            Class.grade_level == new_grade,
            Class.section == new_section,
            Class.id != class_record.id,
        )
    )

    if duplicate is not None:
        raise ValueError(
            "A class with this grade and section already exists."
        )

    class_record.name = new_name
    class_record.grade_level = new_grade
    class_record.section = new_section

    try:
        db.commit()
        db.refresh(class_record)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "A class with this grade and section already exists."
        ) from None

    return class_record


def deactivate(db: Session, class_record: Class) -> Class:
    if not class_record.is_active:
        raise ValueError("Class is already inactive.")

    class_record.is_active = False

    try:
        db.commit()
        db.refresh(class_record)
    except IntegrityError:
        db.rollback()
        raise ValueError("Unable to deactivate class.") from None

    return class_record
