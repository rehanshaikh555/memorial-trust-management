from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.schemas.academic_year import (
    AcademicYearCreate,
    AcademicYearResponse,
    AcademicYearUpdate,
    SchoolAcademicYearCreate,
    SchoolAcademicYearResponse,
)
from app.schemas.school import SchoolResponse
from app.services import academic_year_service as AcademicYearService
from app.services.scope_service import has_school_access, has_trust_access


router = APIRouter(
    prefix="/academic-years",
    tags=["Academic Years"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_CREATE.value
            )
        )
    ],
)
def create_academic_year(
    data: AcademicYearCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> AcademicYearResponse:
    if not has_trust_access(
        db,
        current_user,
        data.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    try:
        academic_year = AcademicYearService.create(
            db,
            trust_id=data.trust_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return academic_year


@router.get(
    "",
    response_model=list[AcademicYearResponse],
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_READ.value
            )
        )
    ],
)
def list_academic_years(
    trust_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[AcademicYearResponse]:
    if not has_trust_access(
        db,
        current_user,
        trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    return AcademicYearService.list_all(
        db,
        trust_id=trust_id,
    )


@router.get(
    "/{academic_year_id}",
    response_model=AcademicYearResponse,
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_READ.value
            )
        )
    ],
)
def get_academic_year(
    academic_year_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AcademicYearResponse:
    academic_year = AcademicYearService.get_by_id(
        db,
        academic_year_id,
    )

    if academic_year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        )

    if not has_trust_access(
        db,
        current_user,
        academic_year.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    return academic_year


@router.patch(
    "/{academic_year_id}",
    response_model=AcademicYearResponse,
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_UPDATE.value
            )
        )
    ],
)
def update_academic_year(
    academic_year_id: UUID,
    data: AcademicYearUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> AcademicYearResponse:
    academic_year = AcademicYearService.get_by_id(
        db,
        academic_year_id,
    )

    if academic_year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        )

    if not has_trust_access(
        db,
        current_user,
        academic_year.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    try:
        return AcademicYearService.update(
            db,
            academic_year,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{academic_year_id}/set-current",
    response_model=AcademicYearResponse,
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_SET_CURRENT.value
            )
        )
    ],
)
def set_current_academic_year(
    academic_year_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AcademicYearResponse:
    academic_year = AcademicYearService.get_by_id(
        db,
        academic_year_id,
    )

    if academic_year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        )

    if not has_trust_access(
        db,
        current_user,
        academic_year.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    try:
        return AcademicYearService.set_current(
            db,
            academic_year,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{academic_year_id}/deactivate",
    response_model=AcademicYearResponse,
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_DEACTIVATE.value
            )
        )
    ],
)
def deactivate_academic_year(
    academic_year_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> AcademicYearResponse:
    academic_year = AcademicYearService.get_by_id(
        db,
        academic_year_id,
    )

    if academic_year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        )

    if not has_trust_access(
        db,
        current_user,
        academic_year.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    try:
        return AcademicYearService.deactivate(
            db,
            academic_year,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{academic_year_id}/schools",
    response_model=SchoolAcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_UPDATE.value
            )
        )
    ],
)
def attach_school_to_academic_year(
    academic_year_id: UUID,
    data: SchoolAcademicYearCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> SchoolAcademicYearResponse:
    academic_year = AcademicYearService.get_by_id(
        db,
        academic_year_id,
    )

    if academic_year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        )

    if not has_trust_access(
        db,
        current_user,
        academic_year.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    if not has_school_access(
        db,
        current_user,
        data.school_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this school.",
        )

    try:
        association = AcademicYearService.attach_school(
            db,
            academic_year,
            data.school_id,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return association


@router.get(
    "/{academic_year_id}/schools",
    response_model=list[SchoolResponse],
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_READ.value
            )
        )
    ],
)
def list_academic_year_schools(
    academic_year_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[SchoolResponse]:
    academic_year = AcademicYearService.get_by_id(
        db,
        academic_year_id,
    )

    if academic_year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        )

    if not has_trust_access(
        db,
        current_user,
        academic_year.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    return AcademicYearService.list_schools(
        db,
        academic_year_id,
    )


@router.delete(
    "/{academic_year_id}/schools/{school_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(
            require_permission(
                Permission.ACADEMIC_YEAR_UPDATE.value
            )
        )
    ],
)
def detach_school_from_academic_year(
    academic_year_id: UUID,
    school_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    academic_year = AcademicYearService.get_by_id(
        db,
        academic_year_id,
    )

    if academic_year is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found.",
        )

    if not has_trust_access(
        db,
        current_user,
        academic_year.trust_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trust.",
        )

    if not has_school_access(
        db,
        current_user,
        school_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this school.",
        )

    try:
        AcademicYearService.detach_school(
            db,
            academic_year,
            school_id,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
