from app.models.academic_year import AcademicYear
from app.models.class_model import Class
from app.models.document_verification import DocumentVerification
from app.models.enrollment import Enrollment
from app.models.guardian import Guardian
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.school import School
from app.models.school_academic_year import SchoolAcademicYear
from app.models.student import Student
from app.models.student_document import StudentDocument
from app.models.student_guardian import StudentGuardian
from app.models.trust import Trust
from app.models.user import User
from app.models.user_school_access import UserSchoolAccess

__all__ = [
    "AcademicYear",
    "Class",
    "DocumentVerification",
    "Enrollment",
    "Guardian",
    "Permission",
    "Role",
    "RolePermission",
    "School",
    "SchoolAcademicYear",
    "Student",
    "StudentDocument",
    "StudentGuardian",
    "Trust",
    "User",
    "UserSchoolAccess",
    "Teacher",
    "TeacherAssignment",
    "SchoolCalendar",
    "Attendance",
    "TeacherAttendance",


]
from app.models.teacher import Teacher
from app.models.teacher_assignment import TeacherAssignment


from app.models.school_calendar import SchoolCalendar
from app.models.attendance import Attendance
from app.models.teacher_attendance import TeacherAttendance
