from datetime import date
from uuid import UUID

from sqlalchemy import select, update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear


def get_by_id(
    db: Session,
    academic_year_id: UUID,
) -> AcademicYear | None:
    return db.scalar(
        select(AcademicYear).where(
            AcademicYear.id == academic_year_id
        )
    )


def require_by_id(
    db: Session,
    academic_year_id: UUID,
) -> AcademicYear:
    academic_year = get_by_id(db, academic_year_id)

    if academic_year is None:
        raise LookupError("Academic year not found.")

    return academic_year


def list_all(
    db: Session,
    trust_id: UUID,
    include_inactive: bool = False,
) -> list[AcademicYear]:
    statement = select(AcademicYear).where(
        AcademicYear.trust_id == trust_id
    )

    if not include_inactive:
        statement = statement.where(
            AcademicYear.is_active.is_(True)
        )

    statement = statement.order_by(
        AcademicYear.start_date.desc()
    )

    return list(db.scalars(statement).all())


def _validate_dates(
    start_date: date,
    end_date: date,
) -> None:
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")


def _clear_current(
    db: Session,
    trust_id: UUID,
) -> None:
    db.execute(
        sa_update(AcademicYear)
        .where(
            AcademicYear.trust_id == trust_id,
            AcademicYear.is_current.is_(True),
        )
        .values(is_current=False)
    )


def create(
    db: Session,
    trust_id: UUID,
    name: str,
    start_date: date,
    end_date: date,
    is_current: bool = False,
) -> AcademicYear:
    _validate_dates(start_date, end_date)

    existing = db.scalar(
        select(AcademicYear).where(
            AcademicYear.trust_id == trust_id,
            AcademicYear.name == name,
        )
    )

    if existing is not None:
        raise ValueError(
            "An academic year with this name already exists."
        )

    if is_current:
        _clear_current(db, trust_id)

    academic_year = AcademicYear(
        trust_id=trust_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        is_current=is_current,
        is_active=True,
    )

    db.add(academic_year)

    try:
        db.commit()
        db.refresh(academic_year)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "An academic year with this name already exists."
        )

    return academic_year


def update(
    db: Session,
    academic_year: AcademicYear,
    name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AcademicYear:
    new_name = (
        name if name is not None
        else academic_year.name
    )

    new_start = (
        start_date
        if start_date is not None
        else academic_year.start_date
    )

    new_end = (
        end_date
        if end_date is not None
        else academic_year.end_date
    )

    _validate_dates(new_start, new_end)

    if new_name != academic_year.name:
        existing = db.scalar(
            select(AcademicYear).where(
                AcademicYear.trust_id == academic_year.trust_id,
                AcademicYear.name == new_name,
                AcademicYear.id != academic_year.id,
            )
        )

        if existing is not None:
            raise ValueError(
                "An academic year with this name already exists."
            )

    academic_year.name = new_name
    academic_year.start_date = new_start
    academic_year.end_date = new_end

    try:
        db.commit()
        db.refresh(academic_year)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "An academic year with this name already exists."
        )

    return academic_year


def set_current(
    db: Session,
    academic_year: AcademicYear,
) -> AcademicYear:
    if not academic_year.is_active:
        raise ValueError(
            "An inactive academic year cannot be current."
        )

    _clear_current(db, academic_year.trust_id)

    academic_year.is_current = True

    try:
        db.commit()
        db.refresh(academic_year)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Unable to set academic year as current."
        )

    return academic_year


def deactivate(
    db: Session,
    academic_year: AcademicYear,
) -> AcademicYear:
    if not academic_year.is_active:
        raise ValueError(
            "Academic year is already inactive."
        )

    academic_year.is_active = False
    academic_year.is_current = False

    try:
        db.commit()
        db.refresh(academic_year)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Unable to deactivate academic year."
        )

    return academic_year


def attach_school(
    db: Session,
    academic_year: AcademicYear,
    school_id: UUID,
) -> SchoolAcademicYear:
    if not academic_year.is_active:
        raise ValueError(
            "Inactive academic year cannot have schools attached."
        )

    school = db.scalar(
        select(School).where(
            School.id == school_id
        )
    )

    if school is None:
        raise LookupError("School not found.")

    if school.trust_id != academic_year.trust_id:
        raise PermissionError(
            "School does not belong to this trust."
        )

    if not school.is_active:
        raise ValueError(
            "Inactive school cannot be attached."
        )

    existing = db.get(
        SchoolAcademicYear,
        (school_id, academic_year.id),
    )

    if existing is not None:
        raise ValueError(
            "School is already attached to this academic year."
        )

    association = SchoolAcademicYear(
        school_id=school_id,
        academic_year_id=academic_year.id,
    )

    db.add(association)

    try:
        db.commit()
        db.refresh(association)
    except IntegrityError:
        db.rollback()
        raise ValueError(
            "School is already attached to this academic year."
        )

    return association


def detach_school(
    db: Session,
    academic_year: AcademicYear,
    school_id: UUID,
) -> None:
    association = db.get(
        SchoolAcademicYear,
        (school_id, academic_year.id),
    )

    if association is None:
        raise LookupError(
            "School is not attached to this academic year."
        )

    db.delete(association)
    db.commit()


def list_schools(
    db: Session,
    academic_year_id: UUID,
) -> list[School]:
    statement = (
        select(School)
        .join(
            SchoolAcademicYear,
            SchoolAcademicYear.school_id == School.id,
        )
        .where(
            SchoolAcademicYear.academic_year_id
            == academic_year_id
        )
        .order_by(School.name)
    )

    return list(db.scalars(statement).all())
