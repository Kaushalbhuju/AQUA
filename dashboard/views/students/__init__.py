"""
Student views package - modular split from student_views.py
"""

# Registration views
from .registration import student_registration, agent_student_registration

# Management views
from .management import (
    registration_success,
    student_list,
    student_detail,
    agent_student_detail,
    student_application_detail,
    all_candidates,
    biodata,
)

# Approval views
from .approval import (
    approve_student_page,
    decline_student_page,
    approve_student,
    decline_student,
    approval_success,
    update_student_status,
)

# PDF views
from .pdf import (
    generate_student_pdf,
    generate_student_pdf_portal,
    generate_admission_fee_pdf,
    generate_admission_fee_pdf_portal,
)

# Debug (optional, remove in production)
# from .debug import test_form_submission

__all__ = [
    # Registration
    'student_registration',
    'agent_student_registration',
    # Management
    'registration_success',
    'student_list',
    'student_detail',
    'agent_student_detail',
    'student_application_detail',
    'all_candidates',
    'biodata',
    # Approval
    'approve_student_page',
    'decline_student_page',
    'approve_student',
    'decline_student',
    'approval_success',
    'update_student_status',
    # PDF
    'generate_student_pdf',
    'generate_student_pdf_portal',
    'generate_admission_fee_pdf',
    'generate_admission_fee_pdf_portal',
]