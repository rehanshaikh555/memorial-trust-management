from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.models.class_model import Class
from app.models.school import School
from app.models.user_school_access import UserSchoolAccess
from app.schemas.class_model import ClassCreate, ClassResponse, ClassUpdate
from app.services.authorization_service import has_permission
from app.services.class_service import (
    create,
    deactivate,
    get_by_id,
    list_all,
    update,
)
from app.services.scope_service import (
    SUPER_ADMIN,
    SCHOOL_ADMIN,
    TEACHER,
    TRUST_ADMIN,
    VIEWER,
    get_user_role,
    has_school_access,
)

router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)

DbSession = Annotated[Session, Depends(get_db)]


def _require_class_access(
    db: Session,
    current_user,
    class_record: Class,
) -> None:
    if not has_school_access(
        db,
        current_user,
        class_record.school_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this school's class data.",
        )


@router.post(
    "",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_permission(
                Permission.CLASS_CREATE.value
            )
        )
    ],
)
def create_class(
    data: ClassCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ClassResponse:
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
        return create(db, data)
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


@router.get(
    "",
    response_model=list[ClassResponse],
    dependencies=[
        Depends(
            require_permission(
                Permission.CLASS_READ.value
            )
        )
    ],
)
def list_classes(
    db: DbSession,
    current_user: CurrentUser,
    school_id: UUID | None = Query(default=None),
    academic_year_id: UUID | None = Query(default=None),
    include_inactive: bool = Query(default=False),
) -> list[ClassResponse]:
    role = get_user_role(db, current_user)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role could not be resolved.",
        )

    statement = select(Class).join(
        School,
        School.id == Class.school_id,
    )

    if academic_year_id is not None:
        statement = statement.where(
            Class.academic_year_id == academic_year_id
        )

    if not include_inactive:
        statement = statement.where(
            Class.is_active.is_(True)
        )

    if school_id is not None:
        if not has_school_access(
            db,
            current_user,
            school_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this school.",
            )

        statement = statement.where(
            Class.school_id == school_id
        )

    elif role.name == SUPER_ADMIN:
        pass

    elif role.name == TRUST_ADMIN:
        if current_user.trust_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not assigned to a trust.",
            )

        statement = statement.where(
            School.trust_id == current_user.trust_id
        )

    elif role.name in {
        SCHOOL_ADMIN,
        TEACHER,
        VIEWER,
    }:
        statement = statement.join(
            UserSchoolAccess,
            UserSchoolAccess.school_id == Class.school_id,
        ).where(
            UserSchoolAccess.user_id == current_user.id
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsupported role scope.",
        )

    statement = statement.order_by(
        Class.grade_level.asc(),
        Class.section.asc().nullsfirst(),
        Class.name.asc(),
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{class_id}",
    response_model=ClassResponse,
    dependencies=[
        Depends(
            require_permission(
                Permission.CLASS_READ.value
            )
        )
    ],
)
def get_class(
    class_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ClassResponse:
    class_record = get_by_id(db, class_id)

    if class_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    _require_class_access(
        db,
        current_user,
        class_record,
    )

    return class_record


@router.patch(
    "/{class_id}",
    response_model=ClassResponse,
    dependencies=[
        Depends(
            require_permission(
                Permission.CLASS_UPDATE.value
            )
        )
    ],
)
def update_class(
    class_id: UUID,
    data: ClassUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ClassResponse:
    class_record = get_by_id(db, class_id)

    if class_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    _require_class_access(
        db,
        current_user,
        class_record,
    )

    try:
        return update(
            db,
            class_record,
            data,
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


@router.post(
    "/{class_id}/deactivate",
    response_model=ClassResponse,
    dependencies=[
        Depends(
            require_permission(
                Permission.CLASS_DEACTIVATE.value
            )
        )
    ],
)
def deactivate_class(
    class_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ClassResponse:
    class_record = get_by_id(db, class_id)

    if class_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    _require_class_access(
        db,
        current_user,
        class_record,
    )

    try:
        return deactivate(
            db,
            class_record,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
