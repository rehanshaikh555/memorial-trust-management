from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.models.activity import Activity
from app.models.activity_photo import ActivityPhoto
from app.models.audit_log import AuditLog
from app.models.school import School
from app.models.role import Role
from app.models.school_academic_year import SchoolAcademicYear
from app.models.user import User
from app.models.user_school_access import UserSchoolAccess
from app.schemas.activity import ActivityCreate, ActivityUpdate


DRAFT = "DRAFT"
SUBMITTED = "SUBMITTED"
APPROVED = "APPROVED"
REJECTED = "REJECTED"
PUBLISHED = "PUBLISHED"

INTERNAL = "INTERNAL"
PUBLIC = "PUBLIC"


def _audit(
    db: Session,
    *,
    actor_user_id: UUID,
    action: str,
    entity_id: UUID | None,
    school_id: UUID | None,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type="ACTIVITY",
            entity_id=entity_id,
            school_id=school_id,
            old_values=old_values,
            new_values=new_values,
            occurred_at=datetime.now(timezone.utc),
        )
    )


def get_by_id(db: Session, activity_id: UUID) -> Activity | None:
    return db.get(Activity, activity_id)


def validate_school_year(
    db: Session,
    *,
    school_id: UUID,
    academic_year_id: UUID,
) -> None:
    school = db.get(School, school_id)

    if school is None:
        raise LookupError("School not found.")

    if not school.is_active:
        raise ValueError("Cannot use an inactive school.")

    academic_year = db.get(AcademicYear, academic_year_id)

    if academic_year is None:
        raise LookupError("Academic year not found.")

    link = db.scalar(
        select(SchoolAcademicYear).where(
            SchoolAcademicYear.school_id == school_id,
            SchoolAcademicYear.academic_year_id == academic_year_id,
        )
    )

    if link is None:
        raise ValueError(
            "Academic year is not configured for this school."
        )


def create(
    db: Session,
    data: ActivityCreate,
    *,
    actor_user_id: UUID,
) -> Activity:
    validate_school_year(
        db,
        school_id=data.school_id,
        academic_year_id=data.academic_year_id,
    )

    if data.visibility not in {INTERNAL, PUBLIC}:
        raise ValueError("Invalid activity visibility.")

    activity = Activity(
        school_id=data.school_id,
        academic_year_id=data.academic_year_id,
        title=data.title.strip(),
        description=data.description,
        activity_date=data.activity_date,
        activity_type=data.activity_type.strip(),
        status=DRAFT,
        visibility=data.visibility,
        created_by=actor_user_id,
    )

    db.add(activity)
    db.flush()

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_CREATED",
        entity_id=activity.id,
        school_id=activity.school_id,
        new_values={
            "status": DRAFT,
            "title": activity.title,
        },
    )

    db.commit()
    db.refresh(activity)

    return activity


def list_activities(
    db: Session,
    *,
    school_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    status: str | None = None,
) -> list[Activity]:
    statement = select(Activity)

    if school_id is not None:
        statement = statement.where(Activity.school_id == school_id)

    if academic_year_id is not None:
        statement = statement.where(
            Activity.academic_year_id == academic_year_id
        )

    if status is not None:
        statement = statement.where(Activity.status == status)

    statement = statement.order_by(
        Activity.activity_date.desc(),
        Activity.created_at.desc(),
    )

    return list(db.scalars(statement).all())


def update(
    db: Session,
    activity: Activity,
    data: ActivityUpdate,
    *,
    actor_user_id: UUID,
) -> Activity:
    if activity.status == PUBLISHED:
        raise ValueError("Published activities cannot be modified.")

    if activity.status not in {DRAFT, REJECTED}:
        raise ValueError(
            "Only draft or rejected activities can be modified."
        )

    values = data.model_dump(exclude_unset=True)

    if "title" in values and values["title"] is not None:
        activity.title = values["title"].strip()

    if "description" in values:
        activity.description = values["description"]

    if "activity_date" in values and values["activity_date"] is not None:
        activity.activity_date = values["activity_date"]

    if "activity_type" in values and values["activity_type"] is not None:
        activity.activity_type = values["activity_type"].strip()

    if "visibility" in values and values["visibility"] is not None:
        if values["visibility"] not in {INTERNAL, PUBLIC}:
            raise ValueError("Invalid activity visibility.")
        activity.visibility = values["visibility"]

    if activity.status == REJECTED:
        activity.status = DRAFT
        activity.rejection_reason = None
        activity.reviewed_by = None
        activity.reviewed_at = None

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_UPDATED",
        entity_id=activity.id,
        school_id=activity.school_id,
        new_values={
            "status": activity.status,
            "title": activity.title,
        },
    )

    db.commit()
    db.refresh(activity)

    return activity


def submit(
    db: Session,
    activity: Activity,
    *,
    actor_user_id: UUID,
    commit: bool = True,
) -> Activity:
    if activity.status not in {DRAFT, REJECTED}:
        raise ValueError(
            "Only draft or rejected activities can be submitted."
        )

    old_status = activity.status
    activity.status = SUBMITTED
    activity.rejection_reason = None

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_SUBMITTED",
        entity_id=activity.id,
        school_id=activity.school_id,
        old_values={"status": old_status},
        new_values={"status": SUBMITTED},
    )

    if commit:
        db.commit()
        db.refresh(activity)

    return activity


def approve(
    db: Session,
    activity: Activity,
    *,
    actor_user_id: UUID,
    commit: bool = True,
) -> Activity:
    if activity.status != SUBMITTED:
        raise ValueError("Only submitted activities can be approved.")

    activity.status = APPROVED
    activity.reviewed_by = actor_user_id
    activity.reviewed_at = datetime.now(timezone.utc)
    activity.rejection_reason = None

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_APPROVED",
        entity_id=activity.id,
        school_id=activity.school_id,
        old_values={"status": SUBMITTED},
        new_values={"status": APPROVED},
    )

    if commit:
        db.commit()
        db.refresh(activity)

    return activity


def reject(
    db: Session,
    activity: Activity,
    *,
    actor_user_id: UUID,
    reason: str,
    commit: bool = True,
) -> Activity:
    reason = reason.strip()

    if activity.status != SUBMITTED:
        raise ValueError("Only submitted activities can be rejected.")

    if not reason:
        raise ValueError("Rejection reason is required.")

    activity.status = REJECTED
    activity.reviewed_by = actor_user_id
    activity.reviewed_at = datetime.now(timezone.utc)
    activity.rejection_reason = reason

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_REJECTED",
        entity_id=activity.id,
        school_id=activity.school_id,
        new_values={
            "status": REJECTED,
            "rejection_reason": reason,
        },
    )

    if commit:
        db.commit()
        db.refresh(activity)

    return activity


def publish(
    db: Session,
    activity: Activity,
    *,
    actor_user_id: UUID,
    commit: bool = True,
) -> Activity:
    if activity.status != APPROVED:
        raise ValueError("Only approved activities can be published.")

    activity.status = PUBLISHED
    activity.published_at = datetime.now(timezone.utc)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_PUBLISHED",
        entity_id=activity.id,
        school_id=activity.school_id,
        old_values={"status": APPROVED},
        new_values={"status": PUBLISHED},
    )

    if commit:
        db.commit()
        db.refresh(activity)

    return activity


def add_photo(
    db: Session,
    activity: Activity,
    *,
    actor_user_id: UUID,
    file_name: str,
    storage_path: str,
    mime_type: str,
    file_size: int,
    caption: str | None,
    display_order: int,
) -> ActivityPhoto:
    if activity.status == PUBLISHED:
        raise ValueError(
            "Published activities cannot receive new photos."
        )

    photo = ActivityPhoto(
        activity_id=activity.id,
        file_name=file_name,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size=file_size,
        caption=caption,
        display_order=display_order,
        uploaded_by=actor_user_id,
    )

    db.add(photo)
    db.flush()

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_PHOTO_ADDED",
        entity_id=activity.id,
        school_id=activity.school_id,
        new_values={"photo_id": str(photo.id)},
    )

    db.commit()
    db.refresh(photo)

    return photo


def list_photos(
    db: Session,
    activity_id: UUID,
) -> list[ActivityPhoto]:
    statement = (
        select(ActivityPhoto)
        .where(ActivityPhoto.activity_id == activity_id)
        .order_by(
            ActivityPhoto.display_order.asc(),
            ActivityPhoto.created_at.asc(),
        )
    )

    return list(db.scalars(statement).all())


def get_photo(
    db: Session,
    photo_id: UUID,
) -> ActivityPhoto | None:
    return db.get(ActivityPhoto, photo_id)


def delete_photo(
    db: Session,
    activity: Activity,
    photo: ActivityPhoto,
    *,
    actor_user_id: UUID,
) -> None:
    if photo.activity_id != activity.id:
        raise LookupError("Photo does not belong to this activity.")

    if activity.status == PUBLISHED:
        raise ValueError(
            "Published activities cannot have photos removed."
        )

    db.delete(photo)

    _audit(
        db,
        actor_user_id=actor_user_id,
        action="ACTIVITY_PHOTO_DELETED",
        entity_id=activity.id,
        school_id=activity.school_id,
        new_values={"photo_id": str(photo.id)},
    )

    db.commit()


def get_review_recipients(
    db: Session,
    activity: Activity,
) -> list[UUID]:
    school = db.get(School, activity.school_id)

    if school is None:
        return []

    rows = db.execute(
        select(User.id, User.trust_id, User.role_id)
        .where(User.is_active.is_(True))
    ).all()

    result: list[UUID] = []

    for user_id, trust_id, role_id in rows:
        role = db.scalar(
            select(Role.name).where(Role.id == role_id)
        )

        if role == "SUPER_ADMIN":
            result.append(user_id)

        elif role == "TRUST_ADMIN" and trust_id == school.trust_id:
            result.append(user_id)

        elif role == "SCHOOL_ADMIN":
            access = db.scalar(
                select(UserSchoolAccess.user_id).where(
                    UserSchoolAccess.user_id == user_id,
                    UserSchoolAccess.school_id == activity.school_id,
                )
            )

            if access is not None:
                result.append(user_id)

    return list(dict.fromkeys(result))
