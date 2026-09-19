from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.models.guardian import Guardian
from app.models.role import Role
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.services import student_service as StudentService
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
from app.schemas.student import (
    DocumentDecision,
    DocumentRejection,
    EnrollmentResponse,
    GuardianCreate,
    GuardianResponse,
    GuardianUpdate,
    StudentCreate,
    StudentDetailResponse,
    StudentDocumentCreate,
    StudentDocumentResponse,
    StudentListResponse,
    StudentResponse,
    StudentTransfer,
    StudentUpdate,
)

router = APIRouter(prefix="/students", tags=["Students"])

DbSession = Annotated[Session, Depends(get_db)]

STUDENT_ROLES = {SUPER_ADMIN, TRUST_ADMIN, SCHOOL_ADMIN, TEACHER, VIEWER}


def _student_school_id(db: Session, student: Student) -> UUID | None:
    return StudentService.get_current_school_id(db, student.id)


def _require_student_access(
    db: Session,
    current_user,
    student: Student,
) -> UUID | None:
    school_id = _student_school_id(db, student)

    if school_id is None:
        role = get_user_role(db, current_user)
        if role is not None and role.name == SUPER_ADMIN:
            return None
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student has no active school scope.",
        )

    if not has_school_access(db, current_user, school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this student's school.",
        )

    return school_id


def _detail(db: Session, student: Student) -> StudentDetailResponse:
    guardians = [
        GuardianResponse.model_validate(guardian, from_attributes=True)
        for guardian, _ in StudentService.list_guardians(db, student.id)
    ]

    enrollment = StudentService.get_current_enrollment(db, student.id)

    return StudentDetailResponse(
        **StudentResponse.model_validate(student, from_attributes=True).model_dump(),
        guardians=guardians,
        enrollment=(
            EnrollmentResponse.model_validate(
                enrollment,
                from_attributes=True,
            )
            if enrollment
            else None
        ),
    )


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.STUDENT_CREATE.value))],
)
def create_student(
    data: StudentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    if not has_school_access(db, current_user, data.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this school.",
        )

    try:
        return StudentService.create(
            db,
            actor_user_id=current_user.id,
            student_id=data.student_id,
            first_name=data.first_name,
            middle_name=data.middle_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
            address=data.address,
            school_id=data.school_id,
            academic_year_id=data.academic_year_id,
            class_id=data.class_id,
            enrollment_date=data.enrollment_date,
            guardians=[guardian.model_dump() for guardian in data.guardians],
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[StudentListResponse],
    dependencies=[Depends(require_permission(Permission.STUDENT_READ.value))],
)
def list_students(
    db: DbSession,
    current_user: CurrentUser,
    school_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    class_id: UUID | None = None,
    student_status: str | None = Query(default=None, alias="status"),
    include_inactive: bool = False,
) -> list[StudentListResponse]:
    role = get_user_role(db, current_user)

    if role is None or role.name not in STUDENT_ROLES:
        raise HTTPException(status_code=403, detail="Student access is not configured.")

    trust_id = None

    if role.name == TRUST_ADMIN:
        trust_id = current_user.trust_id
    elif role.name in {SCHOOL_ADMIN, TEACHER, VIEWER}:
        if school_id is None:
            raise HTTPException(
                status_code=400,
                detail="school_id is required for school-scoped users.",
            )
        if not has_school_access(db, current_user, school_id):
            raise HTTPException(status_code=403, detail="You do not have access to this school.")

    if school_id is not None and not has_school_access(
        db,
        current_user,
        school_id,
    ):
        raise HTTPException(status_code=403, detail="You do not have access to this school.")

    rows = StudentService.list_students(
        db,
        trust_id=trust_id,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=class_id,
        status=student_status,
        include_inactive=include_inactive,
    )

    result = []

    for student, enrollment in rows:
        response = StudentListResponse.model_validate(
            student,
            from_attributes=True,
        )

        if enrollment:
            response.school_id = enrollment.school_id
            response.academic_year_id = enrollment.academic_year_id
            response.class_id = enrollment.class_id

        result.append(response)

    return result


@router.get(
    "/{student_id}",
    response_model=StudentDetailResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_READ.value))],
)
def get_student(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentDetailResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    return _detail(db, student)


@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_UPDATE.value))],
)
def update_student(
    student_id: UUID,
    data: StudentUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        return StudentService.update(
            db,
            student,
            actor_user_id=current_user.id,
            values=data.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{student_id}/submit",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_UPDATE.value))],
)
def submit_student(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        return StudentService.submit(
            db,
            student,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{student_id}/ready-for-approval",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_UPDATE.value))],
)
def ready_student(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        return StudentService.prepare_for_approval(
            db,
            student,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{student_id}/approve",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_APPROVE.value))],
)
def approve_student(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        return StudentService.approve(
            db,
            student,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{student_id}/transfer",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_TRANSFER.value))],
)
def transfer_student(
    student_id: UUID,
    data: StudentTransfer,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    if not has_school_access(db, current_user, data.school_id):
        raise HTTPException(status_code=403, detail="You do not have access to the target school.")

    try:
        return StudentService.transfer(
            db,
            student,
            actor_user_id=current_user.id,
            school_id=data.school_id,
            academic_year_id=data.academic_year_id,
            class_id=data.class_id,
            enrollment_date=data.enrollment_date,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{student_id}/exit",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_EXIT.value))],
)
def exit_student(
    student_id: UUID,
    exit_date: date,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        return StudentService.exit_student(
            db,
            student,
            actor_user_id=current_user.id,
            exit_date=exit_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{student_id}/graduate",
    response_model=StudentResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_EXIT.value))],
)
def graduate_student(
    student_id: UUID,
    exit_date: date,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        return StudentService.graduate(
            db,
            student,
            actor_user_id=current_user.id,
            exit_date=exit_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{student_id}/guardians",
    response_model=GuardianResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.STUDENT_UPDATE.value))],
)
def add_guardian(
    student_id: UUID,
    data: GuardianCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> GuardianResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        guardian = StudentService.add_guardian(
            db,
            student,
            actor_user_id=current_user.id,
            **data.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    link = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == guardian.id,
        )
    )

    return GuardianResponse(
        id=guardian.id,
        full_name=guardian.full_name,
        relationship=guardian.relationship,
        phone=guardian.phone,
        email=guardian.email,
        address=guardian.address,
        is_primary=bool(link and link.is_primary),
    )


@router.get(
    "/{student_id}/guardians",
    response_model=list[GuardianResponse],
    dependencies=[Depends(require_permission(Permission.STUDENT_READ.value))],
)
def list_guardians(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[GuardianResponse]:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    return [
        GuardianResponse(
            id=guardian.id,
            full_name=guardian.full_name,
            relationship=guardian.relationship,
            phone=guardian.phone,
            email=guardian.email,
            address=guardian.address,
            is_primary=is_primary,
        )
        for guardian, is_primary in StudentService.list_guardians(db, student.id)
    ]


@router.patch(
    "/{student_id}/guardians/{guardian_id}",
    response_model=GuardianResponse,
    dependencies=[Depends(require_permission(Permission.STUDENT_UPDATE.value))],
)
def update_guardian(
    student_id: UUID,
    guardian_id: UUID,
    data: GuardianUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> GuardianResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    guardian = db.scalar(select(Guardian).where(Guardian.id == guardian_id))

    if guardian is None:
        raise HTTPException(status_code=404, detail="Guardian not found.")

    try:
        updated = StudentService.update_guardian(
            db,
            student,
            guardian,
            actor_user_id=current_user.id,
            values=data.model_dump(exclude_unset=True, exclude={"is_primary"}),
            is_primary=data.is_primary,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    link = db.scalar(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == updated.id,
        )
    )

    return GuardianResponse(
        id=updated.id,
        full_name=updated.full_name,
        relationship=updated.relationship,
        phone=updated.phone,
        email=updated.email,
        address=updated.address,
        is_primary=bool(link and link.is_primary),
    )


@router.delete(
    "/{student_id}/guardians/{guardian_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.STUDENT_UPDATE.value))],
)
def delete_guardian(
    student_id: UUID,
    guardian_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    guardian = db.scalar(select(Guardian).where(Guardian.id == guardian_id))

    if guardian is None:
        raise HTTPException(status_code=404, detail="Guardian not found.")

    try:
        StudentService.remove_guardian(
            db,
            student,
            guardian,
            actor_user_id=current_user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/{student_id}/documents",
    response_model=StudentDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.DOCUMENT_UPLOAD.value))],
)
def add_document(
    student_id: UUID,
    data: StudentDocumentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentDocumentResponse:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    try:
        return StudentService.add_document(
            db,
            student,
            actor_user_id=current_user.id,
            **data.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/{student_id}/documents",
    response_model=list[StudentDocumentResponse],
    dependencies=[Depends(require_permission(Permission.DOCUMENT_READ.value))],
)
def list_documents(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[StudentDocumentResponse]:
    student = StudentService.get_by_id(db, student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    return StudentService.list_documents(db, student.id)


def _document_access(
    db: Session,
    document_id: UUID,
    current_user,
) -> object:
    document = StudentService.get_document(db, document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    student = StudentService.get_by_id(db, document.student_id)

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    _require_student_access(db, current_user, student)

    return document


@router.post(
    "/documents/{document_id}/verify",
    response_model=StudentDocumentResponse,
    dependencies=[Depends(require_permission(Permission.DOCUMENT_VERIFY.value))],
)
def verify_document(
    document_id: UUID,
    data: DocumentDecision,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentDocumentResponse:
    document = _document_access(db, document_id, current_user)

    try:
        return StudentService.verify_document(
            db,
            document,
            actor_user_id=current_user.id,
            remarks=data.remarks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/documents/{document_id}/reject",
    response_model=StudentDocumentResponse,
    dependencies=[Depends(require_permission(Permission.DOCUMENT_REJECT.value))],
)
def reject_document(
    document_id: UUID,
    data: DocumentRejection,
    db: DbSession,
    current_user: CurrentUser,
) -> StudentDocumentResponse:
    document = _document_access(db, document_id, current_user)

    try:
        return StudentService.reject_document(
            db,
            document,
            actor_user_id=current_user.id,
            reason=data.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
