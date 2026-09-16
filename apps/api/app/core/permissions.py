from enum import StrEnum

class Permission(StrEnum):
    TRUST_CREATE = "trust.create"
    TRUST_READ = "trust.read"
    TRUST_UPDATE = "trust.update"

    SCHOOL_CREATE = "school.create"
    SCHOOL_READ = "school.read"
    SCHOOL_UPDATE = "school.update"
    SCHOOL_DEACTIVATE = "school.deactivate"

    STUDENT_CREATE = "student.create"
    STUDENT_READ = "student.read"
    STUDENT_UPDATE = "student.update"
    STUDENT_APPROVE = "student.approve"
    STUDENT_TRANSFER = "student.transfer"
    STUDENT_EXIT = "student.exit"

    DOCUMENT_READ = "document.read"
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_VERIFY = "document.verify"
    DOCUMENT_REJECT = "document.reject"

    TEACHER_CREATE = "teacher.create"
    TEACHER_READ = "teacher.read"
    TEACHER_UPDATE = "teacher.update"
    TEACHER_ASSIGN = "teacher.assign"

    ATTENDANCE_CREATE = "attendance.create"
    ATTENDANCE_READ = "attendance.read"
    ATTENDANCE_CORRECT = "attendance.correct"

    ACTIVITY_CREATE = "activity.create"
    ACTIVITY_READ = "activity.read"
    ACTIVITY_UPDATE = "activity.update"
    ACTIVITY_SUBMIT = "activity.submit"
    ACTIVITY_APPROVE = "activity.approve"
    ACTIVITY_PUBLISH = "activity.publish"

    REPORT_READ = "report.read"
    REPORT_GENERATE = "report.generate"

    AUDIT_READ = "audit.read"
