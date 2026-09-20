from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, get_db, require_permission
from app.core.permissions import Permission
from app.schemas.attendance import (
    AttendanceBulkResponse,
    AttendanceCorrectionCreate,
    AttendanceCorrectionResponse,
    AttendanceCorrectionReview,
    AttendanceItem,
    AttendanceSheetResponse,
    BulkAttendanceRequest,
    CalendarCreate,
    CalendarResponse,
    CalendarUpdate,
    MonthlyAttendanceReport,
    YearlyAttendanceReport,
)
from app.services import attendance_service
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(exc, LookupError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


@router.get(
    "/sheet",
    response_model=AttendanceSheetResponse,
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_READ))],
)
def get_sheet(
    school_id: UUID,
    academic_year_id: UUID,
    class_id: UUID,
    attendance_date: date,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return attendance_service.get_sheet(
            db,
            actor=current_user,
            school_id=school_id,
            academic_year_id=academic_year_id,
            class_id=class_id,
            attendance_date=attendance_date,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.post(
    "/bulk",
    response_model=AttendanceBulkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_CREATE))],
)
def bulk_attendance(
    payload: BulkAttendanceRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        records = attendance_service.bulk_mark(
            db,
            actor=current_user,
            school_id=payload.school_id,
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            attendance_date=payload.attendance_date,
            entries=[
                item.model_dump()
                for item in payload.entries
            ],
        )

        rows = attendance_service.list_attendance(
            db,
            actor=current_user,
            school_id=payload.school_id,
            academic_year_id=payload.academic_year_id,
            class_id=payload.class_id,
            start_date=payload.attendance_date,
            end_date=payload.attendance_date,
        )

        return {
            "attendance_date": payload.attendance_date,
            "count": len(records),
            "items": rows,
        }
    except Exception as exc:
        raise _error(exc) from exc


@router.get(
    "",
    response_model=list[AttendanceItem],
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_READ))],
)
def list_attendance(
    school_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year_id: UUID | None = None,
    class_id: UUID | None = None,
    student_id: UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    try:
        return attendance_service.list_attendance(
            db,
            actor=current_user,
            school_id=school_id,
            academic_year_id=academic_year_id,
            class_id=class_id,
            student_id=student_id,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.post(
    "/corrections",
    response_model=AttendanceCorrectionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_CORRECT))],
)
def request_correction(
    payload: AttendanceCorrectionCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return attendance_service.request_correction(
            db,
            actor=current_user,
            attendance_id=payload.attendance_id,
            requested_status=payload.requested_status,
            requested_remarks=payload.requested_remarks,
            reason=payload.reason,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.get(
    "/corrections",
    response_model=list[AttendanceCorrectionResponse],
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_CORRECT))],
)
def list_corrections(
    school_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    correction_status: str | None = Query(default=None, alias="status"),
):
    try:
        return attendance_service.list_corrections(
            db,
            actor=current_user,
            school_id=school_id,
            status=correction_status,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.post(
    "/corrections/{correction_id}/approve",
    response_model=AttendanceCorrectionResponse,
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_CORRECT))],
)
def approve_correction(
    correction_id: UUID,
    payload: AttendanceCorrectionReview,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return attendance_service.approve_correction(
            db,
            actor=current_user,
            correction_id=correction_id,
            review_remarks=payload.remarks,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.post(
    "/corrections/{correction_id}/reject",
    response_model=AttendanceCorrectionResponse,
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_CORRECT))],
)
def reject_correction(
    correction_id: UUID,
    payload: AttendanceCorrectionReview,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return attendance_service.reject_correction(
            db,
            actor=current_user,
            correction_id=correction_id,
            review_remarks=payload.remarks,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.get(
    "/reports/monthly",
    response_model=list[MonthlyAttendanceReport],
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_READ))],
)
def monthly_report(
    school_id: UUID,
    academic_year_id: UUID,
    month: int,
    year: int,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    class_id: UUID | None = None,
    student_id: UUID | None = None,
):
    try:
        return attendance_service.monthly_report(
            db,
            actor=current_user,
            school_id=school_id,
            academic_year_id=academic_year_id,
            month=month,
            year_number=year,
            class_id=class_id,
            student_id=student_id,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.get(
    "/reports/yearly",
    response_model=list[YearlyAttendanceReport],
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_READ))],
)
def yearly_report(
    school_id: UUID,
    academic_year_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    class_id: UUID | None = None,
    student_id: UUID | None = None,
):
    try:
        return attendance_service.yearly_report(
            db,
            actor=current_user,
            school_id=school_id,
            academic_year_id=academic_year_id,
            class_id=class_id,
            student_id=student_id,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.post(
    "/calendar",
    response_model=CalendarResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_CREATE))],
)
def create_calendar(
    payload: CalendarCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return attendance_service.create_calendar(
            db,
            actor=current_user,
            **payload.model_dump(),
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.get(
    "/calendar",
    response_model=list[CalendarResponse],
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_READ))],
)
def list_calendar(
    school_id: UUID,
    academic_year_id: UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None,
):
    try:
        return attendance_service.list_calendar(
            db,
            actor=current_user,
            school_id=school_id,
            academic_year_id=academic_year_id,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.patch(
    "/calendar/{calendar_id}",
    response_model=CalendarResponse,
    dependencies=[Depends(require_permission(Permission.ATTENDANCE_CREATE))],
)
def update_calendar(
    calendar_id: UUID,
    payload: CalendarUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        return attendance_service.update_calendar(
            db,
            actor=current_user,
            calendar_id=calendar_id,
            values=payload.model_dump(exclude_unset=True),
        )
    except Exception as exc:
        raise _error(exc) from exc
