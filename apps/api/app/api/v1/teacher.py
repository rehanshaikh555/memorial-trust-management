from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.services.scope_service import (
    SCHOOL_ADMIN,
    SUPER_ADMIN,
    TEACHER as TEACHER_ROLE,
    TRUST_ADMIN,
    VIEWER,
    get_user_role,
    has_school_access,
    has_trust_access,
)
from app.services import teacher_service as service
from app.schemas.teacher import (
    TeacherAssignmentCreate,
    TeacherAssignmentResponse,
    TeacherAssignmentUpdate,
    TeacherAttendanceCreate,
    TeacherAttendanceResponse,
    TeacherCreate,
    TeacherResponse,
    TeacherUpdate,
)

router = APIRouter(prefix="/teachers", tags=["Teachers"])
Db = Annotated[Session, Depends(get_db)]

SCOPED_ROLES = {
    SCHOOL_ADMIN,
    TEACHER_ROLE,
    VIEWER,
}


def _school_access(db, user, school_id):
    if not has_school_access(db, user, school_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this school.",
        )


def _teacher_access(db, user, teacher_id):
    teacher = service.get_by_id(db, teacher_id)

    if teacher is None:
        raise HTTPException(
            status_code=404,
            detail="Teacher not found.",
        )

    role = get_user_role(db, user)

    if role is None:
        raise HTTPException(
            status_code=403,
            detail="User role is not configured.",
        )

    if role.name == SUPER_ADMIN:
        return teacher

    if role.name == TRUST_ADMIN:
        if not has_trust_access(
            db,
            user,
            teacher.school_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this teacher.",
            )
        return teacher

    if role.name in SCOPED_ROLES:
        if not has_school_access(
            db,
            user,
            teacher.school_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this teacher.",
            )
        return teacher

    raise HTTPException(
        status_code=403,
        detail="You do not have access to this teacher.",
    )


@router.post(
    "",
    response_model=TeacherResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher(
    data: TeacherCreate,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_CREATE)),
    ],
):
    _school_access(
        db,
        current_user,
        data.school_id,
    )

    try:
        return service.create(
            db,
            actor_user_id=current_user.id,
            values=data.model_dump(),
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[TeacherResponse],
)
def list_teachers(
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_READ)),
    ],
    school_id: UUID | None = Query(default=None),
    include_inactive: bool = False,
):
    role = get_user_role(db, current_user)

    if role is None:
        raise HTTPException(
            status_code=403,
            detail="User role is not configured.",
        )

    if school_id is not None:
        _school_access(
            db,
            current_user,
            school_id,
        )

    if role.name in SCOPED_ROLES and school_id is None:
        raise HTTPException(
            status_code=400,
            detail="school_id is required for this role.",
        )

    if role.name == SUPER_ADMIN:
        return service.list_teachers(
            db,
            school_id=school_id,
            include_inactive=include_inactive,
        )

    if role.name == TRUST_ADMIN:
        return service.list_teachers(
            db,
            trust_id=current_user.trust_id,
            school_id=school_id,
            include_inactive=include_inactive,
        )

    return service.list_teachers(
        db,
        school_id=school_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/assignments",
    response_model=list[TeacherAssignmentResponse],
)
def list_assignments(
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_READ)),
    ],
    teacher_id: UUID | None = None,
    school_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    include_inactive: bool = False,
):
    role = get_user_role(db, current_user)

    if role is None:
        raise HTTPException(
            status_code=403,
            detail="User role is not configured.",
        )

    if school_id is not None:
        _school_access(
            db,
            current_user,
            school_id,
        )
    elif role.name in SCOPED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="school_id is required for this role.",
        )

    if teacher_id is not None:
        _teacher_access(
            db,
            current_user,
            teacher_id,
        )

    assignments = service.list_assignments(
        db,
        teacher_id=teacher_id,
        school_id=school_id,
        academic_year_id=academic_year_id,
        include_inactive=include_inactive,
    )

    if role.name == TRUST_ADMIN:
        assignments = [
            assignment
            for assignment in assignments
            if has_trust_access(
                db,
                current_user,
                assignment.school_id,
            )
        ]

    elif role.name in SCOPED_ROLES:
        assignments = [
            assignment
            for assignment in assignments
            if has_school_access(
                db,
                current_user,
                assignment.school_id,
            )
        ]

    return assignments


@router.get(
    "/attendance",
    response_model=list[TeacherAttendanceResponse],
)
def get_teacher_attendance(
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.ATTENDANCE_READ)),
    ],
    teacher_id: UUID | None = None,
    school_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    role = get_user_role(db, current_user)

    if role is None:
        raise HTTPException(
            status_code=403,
            detail="User role is not configured.",
        )

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date.",
        )

    if role.name in SCOPED_ROLES:
        if school_id is None:
            raise HTTPException(
                status_code=400,
                detail="school_id is required for this role.",
            )

        _school_access(
            db,
            current_user,
            school_id,
        )

    elif school_id is not None:
        _school_access(
            db,
            current_user,
            school_id,
        )

    if teacher_id is not None:
        teacher = _teacher_access(
            db,
            current_user,
            teacher_id,
        )

        if school_id is not None and teacher.school_id != school_id:
            raise HTTPException(
                status_code=403,
                detail="Teacher does not belong to the selected school.",
            )

    trust_id = (
        current_user.trust_id
        if role.name == TRUST_ADMIN and school_id is None
        else None
    )

    return service.list_attendance(
        db,
        teacher_id=teacher_id,
        school_id=school_id,
        trust_id=trust_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.post(
    "/assignments",
    response_model=TeacherAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    data: TeacherAssignmentCreate,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_ASSIGN)),
    ],
):
    _school_access(
        db,
        current_user,
        data.school_id,
    )

    _teacher_access(
        db,
        current_user,
        data.teacher_id,
    )

    try:
        return service.create_assignment(
            db,
            actor_user_id=current_user.id,
            **data.model_dump(),
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.patch(
    "/assignments/{assignment_id}",
    response_model=TeacherAssignmentResponse,
)
def update_assignment(
    assignment_id: UUID,
    data: TeacherAssignmentUpdate,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_ASSIGN)),
    ],
):
    assignment = service.get_assignment(
        db,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Teacher assignment not found.",
        )

    _school_access(
        db,
        current_user,
        assignment.school_id,
    )

    _teacher_access(
        db,
        current_user,
        assignment.teacher_id,
    )

    try:
        return service.update_assignment(
            db,
            assignment,
            actor_user_id=current_user.id,
            values=data.model_dump(exclude_unset=True),
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/assignments/{assignment_id}/deactivate",
    response_model=TeacherAssignmentResponse,
)
def deactivate_assignment(
    assignment_id: UUID,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_ASSIGN)),
    ],
):
    assignment = service.get_assignment(
        db,
        assignment_id,
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Teacher assignment not found.",
        )

    _school_access(
        db,
        current_user,
        assignment.school_id,
    )

    _teacher_access(
        db,
        current_user,
        assignment.teacher_id,
    )

    try:
        return service.deactivate_assignment(
            db,
            assignment,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/attendance",
    response_model=TeacherAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_teacher_attendance(
    data: TeacherAttendanceCreate,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.ATTENDANCE_CREATE)),
    ],
    school_id: UUID = Query(...),
):
    _school_access(
        db,
        current_user,
        school_id,
    )

    teacher = _teacher_access(
        db,
        current_user,
        data.teacher_id,
    )

    if teacher.school_id != school_id:
        raise HTTPException(
            status_code=403,
            detail="Teacher does not belong to the selected school.",
        )

    try:
        return service.mark_attendance(
            db,
            school_id=school_id,
            marked_by=current_user.id,
            **data.model_dump(),
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.get(
    "/{teacher_id}",
    response_model=TeacherResponse,
)
def get_teacher(
    teacher_id: UUID,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_READ)),
    ],
):
    return _teacher_access(
        db,
        current_user,
        teacher_id,
    )


@router.patch(
    "/{teacher_id}",
    response_model=TeacherResponse,
)
def update_teacher(
    teacher_id: UUID,
    data: TeacherUpdate,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_UPDATE)),
    ],
):
    teacher = _teacher_access(
        db,
        current_user,
        teacher_id,
    )

    try:
        return service.update(
            db,
            teacher,
            actor_user_id=current_user.id,
            values=data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/{teacher_id}/submit",
    response_model=TeacherResponse,
)
def submit_teacher(
    teacher_id: UUID,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_UPDATE)),
    ],
):
    teacher = _teacher_access(
        db,
        current_user,
        teacher_id,
    )

    try:
        return service.submit(
            db,
            teacher,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/{teacher_id}/ready-for-approval",
    response_model=TeacherResponse,
)
def ready_teacher(
    teacher_id: UUID,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_UPDATE)),
    ],
):
    teacher = _teacher_access(
        db,
        current_user,
        teacher_id,
    )

    try:
        return service.prepare_for_approval(
            db,
            teacher,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/{teacher_id}/approve",
    response_model=TeacherResponse,
)
def approve_teacher(
    teacher_id: UUID,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_UPDATE)),
    ],
):
    teacher = _teacher_access(
        db,
        current_user,
        teacher_id,
    )

    try:
        return service.approve(
            db,
            teacher,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post(
    "/{teacher_id}/deactivate",
    response_model=TeacherResponse,
)
def deactivate_teacher(
    teacher_id: UUID,
    db: Db,
    current_user: CurrentUser,
    _: Annotated[
        object,
        Depends(require_permission(Permission.TEACHER_UPDATE)),
    ],
):
    teacher = _teacher_access(
        db,
        current_user,
        teacher_id,
    )

    try:
        return service.deactivate(
            db,
            teacher,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
