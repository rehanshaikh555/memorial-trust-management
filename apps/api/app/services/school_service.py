from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.school import School
from app.models.user_school_access import UserSchoolAccess
from app.schemas.school import SchoolCreate, SchoolUpdate


class SchoolService:
    @staticmethod
    def create(db: Session, data: SchoolCreate) -> School:
        existing = db.scalar(
            select(School).where(
                School.trust_id == data.trust_id,
                School.code == data.code,
            )
        )

        if existing is not None:
            raise ValueError(
                "A school with this code already exists in this trust."
            )

        school = School(
            trust_id=data.trust_id,
            name=data.name,
            code=data.code,
            address=data.address,
            is_active=True,
        )

        db.add(school)

        try:
            db.commit()
            db.refresh(school)
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "A school with this code already exists in this trust."
            ) from None

        return school

    @staticmethod
    def get_by_id(
        db: Session,
        school_id: UUID,
    ) -> School | None:
        return db.scalar(
            select(School).where(School.id == school_id)
        )

    @staticmethod
    def list_all(
        db: Session,
        *,
        trust_id: UUID | None = None,
        include_inactive: bool = False,
    ) -> list[School]:
        statement = select(School).order_by(School.name.asc())

        if trust_id is not None:
            statement = statement.where(School.trust_id == trust_id)

        if not include_inactive:
            statement = statement.where(School.is_active.is_(True))

        return list(db.scalars(statement).all())

    @staticmethod
    def list_for_user(
        db: Session,
        user_id: UUID,
    ) -> list[School]:
        statement = (
            select(School)
            .join(
                UserSchoolAccess,
                UserSchoolAccess.school_id == School.id,
            )
            .where(
                UserSchoolAccess.user_id == user_id,
                School.is_active.is_(True),
            )
            .order_by(School.name.asc())
        )

        return list(db.scalars(statement).all())
    @staticmethod
    def update(
        db: Session,
        school: School,
        data: SchoolUpdate,
    ) -> School:
        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(school, field, value)

        try:
            db.commit()
            db.refresh(school)
        except IntegrityError:
            db.rollback()
            raise ValueError("Unable to update school.") from None

        return school

    @staticmethod
    def deactivate(
        db: Session,
        school: School,
    ) -> School:
        school.is_active = False

        try:
            db.commit()
            db.refresh(school)
        except IntegrityError:
            db.rollback()
            raise ValueError("Unable to deactivate school.") from None

        return school
    @staticmethod
    def require_by_id(
        db: Session,
        school_id: UUID,
    ) -> School:
        school = SchoolService.get_by_id(db, school_id)

        if school is None:
            raise LookupError("School not found.")

        return school
