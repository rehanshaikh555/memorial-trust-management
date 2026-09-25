from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.student_document import StudentDocument
from app.services import student_service


def make_student(*, status, is_active):
    return Student(
        id=uuid4(),
        student_id=f"STU-{uuid4().hex[:8].upper()}",
        first_name="Test",
        middle_name=None,
        last_name="Student",
        date_of_birth=date(2010, 1, 1),
        gender="Male",
        phone=None,
        email=None,
        address=None,
        status=status,
        is_active=is_active,
    )


def make_verified_document(student_id):
    return StudentDocument(
        id=uuid4(),
        student_id=student_id,
        document_type="BIRTH_CERTIFICATE",
        file_name="birth.pdf",
        storage_path="students/test/birth.pdf",
        mime_type="application/pdf",
        file_size=1000,
        status="VERIFIED",
        rejection_reason=None,
        expiry_date=None,
    )


def test_approval_requires_ready_for_approval_state():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_SUBMITTED,
        is_active=False,
    )

    document = make_verified_document(student.id)

    db.scalars.return_value.all.return_value = [document]

    with pytest.raises(
        ValueError,
        match="ready",
    ):
        student_service.approve(
            db,
            student,
            actor_user_id=uuid4(),
        )


def test_ready_student_can_be_approved():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_READY,
        is_active=False,
    )

    document = make_verified_document(student.id)

    enrollment = MagicMock()
    enrollment.school_id = uuid4()
    enrollment.status = student_service.ENROLLMENT_ACTIVE

    db.scalars.return_value.all.return_value = [document]

    with patch(
        "app.services.student_service.get_current_enrollment",
        return_value=enrollment,
    ):
        result = student_service.approve(
            db,
            student,
            actor_user_id=uuid4(),
        )

    assert result.status == student_service.STATUS_ACTIVE
    assert result.is_active is True


def test_transfer_closes_previous_enrollment():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_ACTIVE,
        is_active=True,
    )

    old_school_id = uuid4()
    new_school_id = uuid4()
    academic_year_id = uuid4()
    old_class_id = uuid4()
    new_class_id = uuid4()

    current = Enrollment(
        id=uuid4(),
        student_id=student.id,
        school_id=old_school_id,
        academic_year_id=academic_year_id,
        class_id=old_class_id,
        enrollment_date=date(2026, 7, 1),
        exit_date=None,
        status=student_service.ENROLLMENT_ACTIVE,
    )

    new_school = MagicMock()
    new_school.id = new_school_id

    with patch(
        "app.services.student_service._validate_enrollment_target",
        return_value=(new_school, MagicMock(), MagicMock()),
    ), patch(
        "app.services.student_service.get_current_enrollment",
        return_value=current,
    ):
        result = student_service.transfer(
            db,
            student,
            actor_user_id=uuid4(),
            school_id=new_school_id,
            academic_year_id=academic_year_id,
            class_id=new_class_id,
            enrollment_date=date(2026, 8, 1),
        )

    assert current.status == student_service.ENROLLMENT_TRANSFERRED
    assert current.exit_date == date(2026, 8, 1)

    created_enrollments = [
        call.args[0]
        for call in db.add.call_args_list
        if isinstance(call.args[0], Enrollment)
    ]

    assert len(created_enrollments) == 1

    new_enrollment = created_enrollments[0]

    assert new_enrollment.student_id == student.id
    assert new_enrollment.school_id == new_school_id
    assert new_enrollment.academic_year_id == academic_year_id
    assert new_enrollment.class_id == new_class_id
    assert new_enrollment.enrollment_date == date(2026, 8, 1)
    assert new_enrollment.status == student_service.ENROLLMENT_ACTIVE

    assert result.status == student_service.STATUS_ACTIVE
    assert result.is_active is True


def test_transfer_rejects_same_enrollment_target():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_ACTIVE,
        is_active=True,
    )

    school_id = uuid4()
    academic_year_id = uuid4()
    class_id = uuid4()

    current = MagicMock()
    current.school_id = school_id
    current.academic_year_id = academic_year_id
    current.class_id = class_id

    target_school = MagicMock()
    target_school.id = school_id

    with patch(
        "app.services.student_service._validate_enrollment_target",
        return_value=(target_school, MagicMock(), MagicMock()),
    ), patch(
        "app.services.student_service.get_current_enrollment",
        return_value=current,
    ), pytest.raises(
        ValueError,
        match="already enrolled",
    ):
        student_service.transfer(
            db,
            student,
            actor_user_id=uuid4(),
            school_id=school_id,
            academic_year_id=academic_year_id,
            class_id=class_id,
            enrollment_date=date(2026, 8, 1),
        )


def test_transfer_does_not_create_second_active_enrollment():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_ACTIVE,
        is_active=True,
    )

    current = MagicMock()
    current.school_id = uuid4()
    current.academic_year_id = uuid4()
    current.class_id = uuid4()
    current.status = student_service.ENROLLMENT_ACTIVE
    current.exit_date = None

    target_school = MagicMock()
    target_school.id = uuid4()

    with patch(
        "app.services.student_service._validate_enrollment_target",
        return_value=(target_school, MagicMock(), MagicMock()),
    ), patch(
        "app.services.student_service.get_current_enrollment",
        return_value=current,
    ):
        student_service.transfer(
            db,
            student,
            actor_user_id=uuid4(),
            school_id=target_school.id,
            academic_year_id=uuid4(),
            class_id=uuid4(),
            enrollment_date=date(2026, 8, 1),
        )

    created = [
        call.args[0]
        for call in db.add.call_args_list
        if isinstance(call.args[0], Enrollment)
    ]

    assert len(created) == 1
    assert created[0].status == student_service.ENROLLMENT_ACTIVE
    assert current.status == student_service.ENROLLMENT_TRANSFERRED


def test_exit_does_not_leave_active_enrollment():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_ACTIVE,
        is_active=True,
    )

    enrollment = MagicMock()
    enrollment.school_id = uuid4()
    enrollment.enrollment_date = date(2026, 7, 1)
    enrollment.status = student_service.ENROLLMENT_ACTIVE
    enrollment.exit_date = None

    with patch(
        "app.services.student_service.get_current_enrollment",
        return_value=enrollment,
    ):
        student_service.exit_student(
            db,
            student,
            actor_user_id=uuid4(),
            exit_date=date(2026, 9, 25),
        )

    assert enrollment.status == student_service.ENROLLMENT_LEFT
    assert enrollment.exit_date == date(2026, 9, 25)
    assert student.status == student_service.STATUS_LEFT
    assert student.is_active is False


def test_graduation_does_not_leave_active_enrollment():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_ACTIVE,
        is_active=True,
    )

    enrollment = MagicMock()
    enrollment.school_id = uuid4()
    enrollment.enrollment_date = date(2026, 7, 1)
    enrollment.status = student_service.ENROLLMENT_ACTIVE
    enrollment.exit_date = None

    with patch(
        "app.services.student_service.get_current_enrollment",
        return_value=enrollment,
    ):
        student_service.graduate(
            db,
            student,
            actor_user_id=uuid4(),
            exit_date=date(2026, 9, 25),
        )

    assert enrollment.status == student_service.ENROLLMENT_GRADUATED
    assert enrollment.exit_date == date(2026, 9, 25)
    assert student.status == student_service.STATUS_GRADUATED
    assert student.is_active is False
