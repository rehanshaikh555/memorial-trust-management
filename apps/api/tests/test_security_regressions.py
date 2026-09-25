from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services import attendance_service
from app.services import notification_service
from app.services import scope_service
from app.services import teacher_service


def _user(*, role_name, trust_id=None, user_id=None):
    role = MagicMock()
    role.name = role_name

    user = MagicMock()
    user.id = user_id or uuid4()
    user.trust_id = trust_id
    user.role_id = uuid4()
    user.is_active = True

    return user, role


def test_teacher_cannot_cross_school_scope():
    trust_id = uuid4()
    requested_school_id = uuid4()

    user, role = _user(
        role_name=scope_service.TEACHER,
        trust_id=trust_id,
    )

    db = MagicMock()

    school = MagicMock()
    school.id = requested_school_id
    school.is_active = True
    school.trust_id = trust_id

    # has_school_access() performs:
    # 1. role lookup
    # 2. school lookup
    # 3. UserSchoolAccess lookup
    db.scalar.side_effect = [
        role,
        school,
        None,
    ]

    assert scope_service.has_school_access(
        db,
        user,
        requested_school_id,
    ) is False


def test_trust_admin_cannot_cross_trust_scope():
    own_trust = uuid4()
    other_trust = uuid4()

    user, role = _user(
        role_name=scope_service.TRUST_ADMIN,
        trust_id=own_trust,
    )

    db = MagicMock()
    db.scalar.return_value = role

    assert scope_service.has_trust_access(
        db,
        user,
        other_trust,
    ) is False


def test_super_admin_can_cross_trust_scope():
    user, role = _user(
        role_name=scope_service.SUPER_ADMIN,
        trust_id=None,
    )

    db = MagicMock()
    db.scalar.return_value = role

    assert scope_service.has_trust_access(
        db,
        user,
        uuid4(),
    ) is True


def test_notification_cannot_be_read_by_non_recipient():
    recipient_id = uuid4()
    attacker_id = uuid4()

    notification = MagicMock()
    notification.id = uuid4()
    notification.recipient_user_id = recipient_id
    notification.is_read = False

    db = MagicMock()

    with pytest.raises(PermissionError, match="notification"):
        notification_service.mark_read(
            db,
            notification,
            user_id=attacker_id,
        )


def test_notification_mark_read_allows_recipient():
    recipient_id = uuid4()

    notification = MagicMock()
    notification.id = uuid4()
    notification.recipient_user_id = recipient_id
    notification.is_read = False

    db = MagicMock()

    result = notification_service.mark_read(
        db,
        notification,
        user_id=recipient_id,
    )

    assert result is notification
    assert notification.is_read is True
    db.commit.assert_called_once()


def test_notification_list_is_user_scoped():
    current_user = uuid4()

    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    result = notification_service.list_for_user(
        db,
        user_id=current_user,
    )

    assert result == []
    db.scalars.assert_called_once()

    stmt = db.scalars.call_args.args[0]
    compiled = str(stmt)

    assert "recipient_user_id" in compiled


def test_notification_unread_count_is_user_scoped():
    current_user = uuid4()

    db = MagicMock()
    db.scalar.return_value = 0

    result = notification_service.unread_count(
        db,
        user_id=current_user,
    )

    assert result == 0
    db.scalar.assert_called_once()

    stmt = db.scalar.call_args.args[0]
    compiled = str(stmt)

    assert "recipient_user_id" in compiled


def test_notification_mark_all_read_is_user_scoped():
    current_user = uuid4()

    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    result = notification_service.mark_all_read(
        db,
        user_id=current_user,
    )

    assert result == 0
    db.scalars.assert_called_once()
    db.commit.assert_called_once()

    stmt = db.scalars.call_args.args[0]
    compiled = str(stmt)

    assert "recipient_user_id" in compiled


def _teacher_and_assignment(
    *,
    school_id,
    academic_year_id,
    class_id,
    user_id,
):
    teacher = MagicMock()
    teacher.id = uuid4()
    teacher.user_id = user_id
    teacher.school_id = school_id
    teacher.is_active = True

    assignment = MagicMock()
    assignment.teacher_id = teacher.id
    assignment.school_id = school_id
    assignment.academic_year_id = academic_year_id
    assignment.class_id = class_id
    assignment.status = "ACTIVE"
    assignment.start_date = date(2026, 1, 1)
    assignment.end_date = None

    return teacher, assignment


def test_teacher_report_scope_rejects_unassigned_class():
    trust_id = uuid4()
    school_id = uuid4()
    academic_year_id = uuid4()
    requested_class_id = uuid4()

    teacher_user, _ = _user(
        role_name=scope_service.TEACHER,
        trust_id=trust_id,
    )

    teacher = MagicMock()
    teacher.id = uuid4()
    teacher.user_id = teacher_user.id
    teacher.school_id = school_id
    teacher.is_active = True

    db = MagicMock()

    role = MagicMock()
    role.name = scope_service.TEACHER

    # _validate_teacher_report_scope() performs:
    # 1. role lookup
    # 2. teacher lookup
    # 3. assignment lookup
    db.scalar.side_effect = [
        role,
        teacher,
        None,
    ]

    with pytest.raises(PermissionError, match="assigned"):
        attendance_service._validate_teacher_report_scope(
            db,
            actor=teacher_user,
            school_id=school_id,
            academic_year_id=academic_year_id,
            class_id=requested_class_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )


def test_teacher_report_scope_allows_assigned_class():
    trust_id = uuid4()
    school_id = uuid4()
    academic_year_id = uuid4()
    assigned_class_id = uuid4()

    teacher_user, _ = _user(
        role_name=scope_service.TEACHER,
        trust_id=trust_id,
    )

    teacher, assignment = _teacher_and_assignment(
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=assigned_class_id,
        user_id=teacher_user.id,
    )

    db = MagicMock()

    role = MagicMock()
    role.name = scope_service.TEACHER

    # _validate_teacher_report_scope() performs:
    # 1. role lookup
    # 2. teacher lookup
    # 3. assignment lookup
    db.scalar.side_effect = [
        role,
        teacher,
        assignment,
    ]

    result = attendance_service._validate_teacher_report_scope(
        db,
        actor=teacher_user,
        school_id=school_id,
        academic_year_id=academic_year_id,
        class_id=assigned_class_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert result is None


def test_teacher_assignment_cannot_belong_to_different_school():
    teacher_id = uuid4()
    requested_school_id = uuid4()
    actual_school_id = uuid4()

    teacher = MagicMock()
    teacher.id = teacher_id
    teacher.school_id = actual_school_id
    teacher.is_active = True
    teacher.status = teacher_service.STATUS_ACTIVE

    db = MagicMock()
    db.scalar.return_value = teacher

    with pytest.raises(ValueError, match="school"):
        teacher_service._validate_assignment_target(
            db,
            teacher_id=teacher_id,
            school_id=requested_school_id,
            academic_year_id=uuid4(),
            class_id=None,
            start_date=date(2026, 1, 1),
            end_date=None,
        )


def test_teacher_attendance_cannot_be_marked_for_different_school():
    teacher_id = uuid4()
    requested_school_id = uuid4()
    actual_school_id = uuid4()

    teacher = MagicMock()
    teacher.id = teacher_id
    teacher.school_id = actual_school_id
    teacher.is_active = True
    teacher.status = teacher_service.STATUS_ACTIVE

    db = MagicMock()
    db.get.return_value = teacher

    with pytest.raises(ValueError, match="school"):
        teacher_service.mark_attendance(
            db,
            teacher_id=teacher_id,
            school_id=requested_school_id,
            attendance_date=date(2026, 1, 1),
            status="PRESENT",
            remarks=None,
            marked_by=uuid4(),
        )
