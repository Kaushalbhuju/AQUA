# dashboard/urls.py
from django.urls import path
from .views.dashboards import *
from .views.students import (
    registration_success, student_registration, student_list, student_detail,
    student_application_detail, update_student_status,
    generate_student_pdf, generate_student_pdf_portal, generate_admission_fee_pdf, 
    generate_admission_fee_pdf_portal, approve_student, decline_student,
    approve_student_page, decline_student_page, biodata, approval_success
)
from .views.other_views import home_view, dashboard_view, profile_view, settings_view
from .views.report_views import teacher_report, export_report_excel, export_report_pdf
from .views.portal_views import (
    PortalStudentRegistrationView, portal_registration_success, portal_logout
)
from .views.ssw_views import months_2026 
from .views.material_views import share_materials, delete_material, view_shared_materials, download_material, public_materials

app_name = 'dashboard'

urlpatterns = [
    # General pages
    path('', home_view, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),

    # Role-based dashboards
    path('operation_head/', operation_head_dashboard, name='operation_head_dashboard'),
    path('manager/', manager_dashboard, name='manager_dashboard'),
    path('staff/', staff_dashboard, name='staff_dashboard'),
    path('college_student/', college_student_dashboard, name='college_student_dashboard'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/student-attendance/', student_attendance, name='student_attendance'),
    path('teacher/save-attendance/', save_attendance_data, name='save_attendance_data'),
    path('teacher/student-records/', student_records, name='student_records'),
    path('teacher/student-records/manage/', manage_teacher_records, name='manage_teacher_records'),
    path('teacher/classes/', class_list, name='class_list'),
    path('teacher/classes/<int:classroom_id>/attendance/', class_attendance, name='class_attendance'),
    path('teacher/classes/<int:classroom_id>/save-attendance/', save_class_attendance, name='save_class_attendance'),
    path('teacher/classes/<int:classroom_id>/students/', manage_class_students, name='manage_class_students'),
    path('teacher/student/<int:student_id>/notes/', student_daily_notes, name='student_daily_notes'),
    path('teacher/student/<int:student_id>/notes/save/', save_daily_note, name='save_daily_note'),
    path('teacher/report/', teacher_report, name='teacher_report'),
    path('teacher/report/export/excel/', export_report_excel, name='export_report_excel'),
    path('teacher/report/export/pdf/', export_report_pdf, name='export_report_pdf'),
    path('recruitment_client/', recruitment_client_dashboard, name='recruitment_client_dashboard'),

    # Student management (Admin/Staff side)
    path('student_registration/', student_registration, name='student_registration'),
    path('biodata/', biodata, name='biodata'),
    path('success/<int:student_id>/', registration_success, name='registration_success'),
    path('students/', student_list, name='student_list'),
    path('students/<int:student_id>/', student_detail, name='student_detail'),

    # Recruitment / client dashboard
    path('recruitment/student/<int:student_id>/', student_application_detail, name='student_application_detail'),
    path('recruitment/student/<int:student_id>/update-status/', update_student_status, name='update_student_status'),
    path('recruitment/move-stage/<int:student_id>/<str:next_stage>/', move_to_next_stage, name='move_to_next_stage'),

    # PDF generation
    path('student/<int:student_id>/pdf/', generate_student_pdf, name='generate_student_pdf'),
    path('student/<int:student_id>/admission-fee-pdf/', generate_admission_fee_pdf, name='generate_admission_fee_pdf'),

    # Approve / decline student
    path('student/<int:student_id>/approve/', approve_student, name='approve_student'),
    path('student/<int:student_id>/decline/', decline_student, name='decline_student'),

    # Detailed approve/decline forms
    path('dashboard/students/<int:student_id>/approve/', approve_student_page, name='approve_student_page'),
    path('dashboard/students/<int:student_id>/decline/', decline_student_page, name='decline_student_page'),

    # Approval success page
    path('approval_success/<int:student_id>/', approval_success, name='approval_success'),

    # Student Registration Portal Routes
    path('portal/register/', PortalStudentRegistrationView.as_view(), name='portal_student_registration'),
    path('portal/success/', portal_registration_success, name='portal_registration_success'),
    path('portal/logout/', portal_logout, name='portal_logout'),
    path('portal/student/<int:student_id>/pdf/', generate_student_pdf_portal, name='generate_student_pdf_portal'),
    path('portal/student/<int:student_id>/admission-fee-pdf/', generate_admission_fee_pdf_portal, name='generate_admission_fee_pdf_portal'),

    # SSW specific views
    path('aggredcs/', months_2026, name='contracts_2026'),

    # Shared Materials
    path('teacher/share-materials/', share_materials, name='share_materials'),
    path('teacher/share-materials/delete/<int:material_id>/', delete_material, name='delete_material'),
    path('materials/', view_shared_materials, name='view_shared_materials'),
    path('materials/download/<int:material_id>/', download_material, name='download_material'),
    path('public/materials/', public_materials, name='public_materials'),
]

