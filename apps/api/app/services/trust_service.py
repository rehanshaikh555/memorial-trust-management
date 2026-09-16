from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.trust import Trust
from app.schemas.trust import TrustCreate, TrustUpdate


class TrustService:
    @staticmethod
    def create(db: Session, data: TrustCreate) -> Trust:
        existing = db.scalar(
            select(Trust).where(Trust.code == data.code)
        )

        if existing is not None:
            raise ValueError("A trust with this code already exists.")

        trust = Trust(
            name=data.name,
            code=data.code,
            description=data.description,
            is_active=True,
        )

        db.add(trust)

        try:
            db.commit()
            db.refresh(trust)
        except IntegrityError:
            db.rollback()
            raise ValueError("A trust with this code already exists.") from None

        return trust

    @staticmethod
    def get_by_id(db: Session, trust_id: UUID) -> Trust | None:
        return db.scalar(
            select(Trust).where(Trust.id == trust_id)
        )

    @staticmethod
    def list_all(db: Session, *, include_inactive: bool = False) -> list[Trust]:
        statement = select(Trust).order_by(Trust.name.asc())

        if not include_inactive:
            statement = statement.where(Trust.is_active.is_(True))

        return list(db.scalars(statement).all())

    @staticmethod
    def update(
        db: Session,
        trust: Trust,
        data: TrustUpdate,
    ) -> Trust:
        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(trust, field, value)

        try:
            db.commit()
            db.refresh(trust)
        except IntegrityError:
            db.rollback()
            raise ValueError("Unable to update trust.") from None

        return trust

    @staticmethod
    def require_by_id(db: Session, trust_id: UUID) -> Trust:
        trust = TrustService.get_by_id(db, trust_id)

        if trust is None:
            raise LookupError("Trust not found.")

        return trust
