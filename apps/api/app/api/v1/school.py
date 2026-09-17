from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.models.trust import Trust
from app.schemas.school import SchoolCreate, SchoolResponse, SchoolUpdate
from app.services.school_service import SchoolService
from app.services.scope_service import (
    SCHOOL_ADMIN,
    SUPER_ADMIN,
    TEACHER,
    TRUST_ADMIN,
    VIEWER,
    get_user_role,
    has_school_access,
    has_trust_access,
)


router = APIRouter(prefix="/schools", tags=["Schools"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=SchoolResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission(Permission.SCHOOL_CREATE.value)),
    ],
)
def create_school(
    data: SchoolCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> SchoolResponse:
    trust = db.get(Trust, data.trust_id)

    if trust is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trust not found.",
        )

    if not trust.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a school under an inactive trust.",
        )

    if not has_trust_access(db, current_user, data.trust_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    try:
        school = SchoolService.create(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return school


@router.get(
    "",
    response_model=list[SchoolResponse],
    dependencies=[
        Depends(require_permission(Permission.SCHOOL_READ.value)),
    ],
)
def list_schools(
    db: DbSession,
    current_user: CurrentUser,
) -> list[SchoolResponse]:
    role = get_user_role(db, current_user)

    if role is None:
        return []

    if role.name == SUPER_ADMIN:
        return SchoolService.list_all(db)

    if role.name == TRUST_ADMIN:
        if current_user.trust_id is None:
            return []

        return SchoolService.list_all(
            db,
            trust_id=current_user.trust_id,
        )

    if role.name in {SCHOOL_ADMIN, TEACHER, VIEWER}:
        return SchoolService.list_for_user(
            db,
            current_user.id,
        )

    return []


@router.post(
    "/{school_id}/deactivate",
    response_model=SchoolResponse,
    dependencies=[
        Depends(require_permission(Permission.SCHOOL_DEACTIVATE.value)),
    ],
)
def deactivate_school(
    school_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> SchoolResponse:
    school = SchoolService.get_by_id(db, school_id)

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    if not has_school_access(db, current_user, school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this school.",
        )

    if not school.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School is already inactive.",
        )

    try:
        school = SchoolService.deactivate(db, school)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return school

@router.get(
    "/{school_id}",
    response_model=SchoolResponse,
    dependencies=[
        Depends(require_permission(Permission.SCHOOL_READ.value)),
    ],
)
def get_school(
    school_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> SchoolResponse:
    school = SchoolService.get_by_id(db, school_id)

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    if not has_school_access(db, current_user, school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this school.",
        )

    return school


@router.patch(
    "/{school_id}",
    response_model=SchoolResponse,
    dependencies=[
        Depends(require_permission(Permission.SCHOOL_UPDATE.value)),
    ],
)
def update_school(
    school_id: UUID,
    data: SchoolUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> SchoolResponse:
    school = SchoolService.get_by_id(db, school_id)

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    if not has_school_access(db, current_user, school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this school.",
        )

    try:
        school = SchoolService.update(db, school, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return school
