"""
Dashboard views package - modular split from dashboard_views_fixed.py
"""
from .role_dashboards import (
    operation_head_dashboard,
    manager_dashboard,
    staff_dashboard,
    college_student_dashboard,
    teacher_dashboard,
)
from .teacher import (
    student_attendance,
    class_list,
    create_class,
    class_attendance,
    save_class_attendance,
    manage_class_students,
    student_daily_notes,
    save_daily_note,
    save_attendance_data,
    student_records,
    manage_teacher_records,
)
from .recruitment import (
    recruitment_client_dashboard,
    move_to_next_stage,
)

__all__ = [
    'operation_head_dashboard',
    'manager_dashboard',
    'staff_dashboard',
    'college_student_dashboard',
    'teacher_dashboard',
    'student_attendance',
    'class_list',
    'create_class',
    'class_attendance',
    'save_class_attendance',
    'manage_class_students',
    'student_daily_notes',
    'save_daily_note',
    'save_attendance_data',
    'student_records',
    'manage_teacher_records',
    'recruitment_client_dashboard',
    'move_to_next_stage',
]