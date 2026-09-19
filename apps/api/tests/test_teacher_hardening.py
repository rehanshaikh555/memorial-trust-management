from datetime import date
from uuid import uuid4
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.schemas.teacher import TeacherCreate, TeacherAssignmentCreate
from app.services import teacher_service


def test_teacher_create_requires_school_scope():
    with pytest.raises(ValueError):
        TeacherCreate(teacher_id="T-1", first_name="Jane")

def test_teacher_create_normalizes_text():
    value = TeacherCreate(
        school_id=uuid4(),
        teacher_id=" T-1 ",
        first_name=" Jane ",
        middle_name=" ",
    )
    assert value.teacher_id == "T-1"
    assert value.first_name == "Jane"
    assert value.middle_name is None


def test_assignment_schema_rejects_reverse_dates():
    with pytest.raises(ValueError):
        TeacherAssignmentCreate(
            teacher_id=uuid4(),
            school_id=uuid4(),
            academic_year_id=uuid4(),
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 1),
        )


def test_assignment_overlap_condition_open_end():
    condition = teacher_service._assignment_overlap_condition(
        date(2026, 8, 10), None
    )
    assert condition is not None


def test_teacher_attendance_statuses_are_restricted():
    assert teacher_service.ATTENDANCE_STATUSES == {
        "PRESENT", "ABSENT", "LEAVE", "HALF_DAY"
    }


def test_approve_audit_captures_previous_status():
    # Regression guard: approve() must construct old_values before mutating the teacher.
    teacher = MagicMock()
    teacher.status = teacher_service.STATUS_READY
    teacher.is_active = False
    db = MagicMock()

    result = teacher_service.approve(db, teacher, actor_user_id=uuid4())
    audit = db.add.call_args.args[0]

    assert audit.old_values == {
        "status": teacher_service.STATUS_READY,
        "is_active": False,
    }
    assert audit.new_values == {
        "status": teacher_service.STATUS_ACTIVE,
        "is_active": True,
    }
    assert result.status == teacher_service.STATUS_ACTIVE