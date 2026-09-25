from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.student import Student
from app.models.student_document import StudentDocument
from app.services import student_service


def make_student(
    *,
    status=student_service.STATUS_DRAFT,
    is_active=False,
):
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


def make_document(*, status="PENDING"):
    return StudentDocument(
        id=uuid4(),
        student_id=uuid4(),
        document_type="BIRTH_CERTIFICATE",
        file_name="birth-certificate.pdf",
        storage_path="students/test/birth-certificate.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=status,
        rejection_reason=None,
        expiry_date=None,
    )


def test_student_status_constants_are_complete():
    expected = {
        "APPLICATION_DRAFT",
        "SUBMITTED",
        "READY_FOR_APPROVAL",
        "ACTIVE",
        "TRANSFERRED",
        "LEFT",
        "GRADUATED",
        "ARCHIVED",
    }

    actual = {
        student_service.STATUS_DRAFT,
        student_service.STATUS_SUBMITTED,
        student_service.STATUS_READY,
        student_service.STATUS_ACTIVE,
        student_service.STATUS_TRANSFERRED,
        student_service.STATUS_LEFT,
        student_service.STATUS_GRADUATED,
        student_service.STATUS_ARCHIVED,
    }

    assert actual == expected


def test_submit_only_accepts_draft():
    db = MagicMock()

    submitted = make_student(status=student_service.STATUS_SUBMITTED)

    with pytest.raises(ValueError, match="draft"):
        student_service.submit(
            db,
            submitted,
            actor_user_id=uuid4(),
        )


def test_ready_for_approval_only_accepts_submitted():
    db = MagicMock()

    draft = make_student(status=student_service.STATUS_DRAFT)

    with pytest.raises(ValueError, match="submitted"):
        student_service.prepare_for_approval(
            db,
            draft,
            actor_user_id=uuid4(),
        )


def test_ready_for_approval_requires_documents():
    db = MagicMock()

    student = make_student(status=student_service.STATUS_SUBMITTED)

    db.scalars.return_value.all.return_value = []

    with pytest.raises(ValueError, match="document"):
        student_service.prepare_for_approval(
            db,
            student,
            actor_user_id=uuid4(),
        )


def test_rejected_document_can_be_verified_again():
    db = MagicMock()

    document = make_document(status="REJECTED")

    result = student_service.verify_document(
        db,
        document,
        actor_user_id=uuid4(),
        remarks="Corrected document verified.",
    )

    assert result.status == "VERIFIED"
    assert result.rejection_reason is None

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(document)


def test_pending_document_can_be_rejected():
    db = MagicMock()

    document = make_document(status="PENDING")

    result = student_service.reject_document(
        db,
        document,
        actor_user_id=uuid4(),
        reason="Document is not readable.",
    )

    assert result.status == "REJECTED"
    assert result.rejection_reason == "Document is not readable."

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(document)


def test_invalid_document_status_cannot_be_rejected():
    db = MagicMock()

    document = make_document(status="REJECTED")

    with pytest.raises(
        ValueError,
        match="pending or verified",
    ):
        student_service.reject_document(
            db,
            document,
            actor_user_id=uuid4(),
            reason="Another rejection.",
        )


def test_invalid_document_status_cannot_be_verified():
    db = MagicMock()

    document = make_document(status="PENDING")
    document.status = "ARCHIVED"

    with pytest.raises(
        ValueError,
        match="pending or rejected",
    ):
        student_service.verify_document(
            db,
            document,
            actor_user_id=uuid4(),
            remarks=None,
        )


def test_exit_requires_active_student():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_LEFT,
        is_active=False,
    )

    with pytest.raises(ValueError):
        student_service.exit_student(
            db,
            student,
            actor_user_id=uuid4(),
            exit_date=date.today(),
        )


def test_graduate_requires_active_student():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_GRADUATED,
        is_active=False,
    )

    with pytest.raises(ValueError):
        student_service.graduate(
            db,
            student,
            actor_user_id=uuid4(),
            exit_date=date.today(),
        )


def test_transfer_requires_active_student():
    db = MagicMock()

    student = make_student(
        status=student_service.STATUS_LEFT,
        is_active=False,
    )

    with pytest.raises(ValueError):
        student_service.transfer(
            db,
            student,
            actor_user_id=uuid4(),
            school_id=uuid4(),
            academic_year_id=uuid4(),
            class_id=uuid4(),
            enrollment_date=date.today(),
        )


def test_active_enrollment_status_constant_is_stable():
    assert student_service.ENROLLMENT_ACTIVE == "ACTIVE"
    assert student_service.ENROLLMENT_TRANSFERRED == "TRANSFERRED"
    assert student_service.ENROLLMENT_LEFT == "LEFT"
    assert student_service.ENROLLMENT_GRADUATED == "GRADUATED"


def test_audit_helper_adds_audit_record():
    db = MagicMock()

    student_id = uuid4()
    school_id = uuid4()
    actor_id = uuid4()

    student_service._audit(
        db,
        actor_user_id=actor_id,
        action="STUDENT_TEST_EVENT",
        entity_type="STUDENT",
        entity_id=student_id,
        school_id=school_id,
        old_values={"status": "SUBMITTED"},
        new_values={"status": "READY_FOR_APPROVAL"},
    )

    db.add.assert_called_once()

    audit = db.add.call_args.args[0]

    assert audit.actor_user_id == actor_id
    assert audit.action == "STUDENT_TEST_EVENT"
    assert audit.entity_type == "STUDENT"
    assert audit.entity_id == student_id
    assert audit.school_id == school_id
    assert audit.old_values == {"status": "SUBMITTED"}
    assert audit.new_values == {"status": "READY_FOR_APPROVAL"}
