from app.core.permissions import Permission


def test_permission_values_are_unique() -> None:
    values = [permission.value for permission in Permission]
    assert len(values) == len(set(values))


def test_permission_catalog_count() -> None:
    assert len(Permission) == 42


def test_required_permissions_exist() -> None:
    assert Permission.TRUST_CREATE.value == "trust.create"
    assert Permission.TRUST_READ.value == "trust.read"
    assert Permission.SCHOOL_READ.value == "school.read"
    assert Permission.STUDENT_READ.value == "student.read"
    assert Permission.DOCUMENT_VERIFY.value == "document.verify"
    assert Permission.TEACHER_ASSIGN.value == "teacher.assign"
    assert Permission.ATTENDANCE_CREATE.value == "attendance.create"
    assert Permission.ACTIVITY_READ.value == "activity.read"
    assert Permission.REPORT_GENERATE.value == "report.generate"
    assert Permission.AUDIT_READ.value == "audit.read"
