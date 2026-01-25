# dashboard/urls.py
from django.urls import path
from .views.dashboard_views import (
    operation_head_dashboard, manager_dashboard, staff_dashboard,
    college_student_dashboard, recruitment_client_dashboard, 
    move_to_next_stage
)
from .views.other_views import home_view, dashboard_view, profile_view, settings_view
from .views.student_views import (
    registration_success, student_registration, student_list, student_detail,
    student_application_detail, update_student_status,
    generate_student_pdf, approve_student, decline_student,
    approve_student_page, decline_student_page, biodata
)
from .views.portal_views import (
    PortalStudentRegistrationView, portal_registration_success
)
from .views.ssw_views import ( months_2026 )

# from .views.agent_views import (
#     # agent_login, agent_logout, 
#     # agent_dashboard, 
#     # agent_student_detail, agent_student_registration
# )

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

    # Approve / decline student
    path('student/<int:student_id>/approve/', approve_student, name='approve_student'),
    path('student/<int:student_id>/decline/', decline_student, name='decline_student'),

    # Detailed approve/decline forms
    path('dashboard/students/<int:student_id>/approve/', approve_student_page, name='approve_student_page'),
    path('dashboard/students/<int:student_id>/decline/', decline_student_page, name='decline_student_page'),

    # REMOVE Agent Dashboard Routes from here
    # path('agent/login/', agent_login, name='agent_login'),
    # # path('agent/logout/', agent_logout, name='agent_logout'),
    # path('agent/dashboard/', agent_dashboard, name='agent_dashboard'),
    # path('agent/student/<int:student_id>/', agent_student_detail, name='agent_student_detail'),
    # path('agent/register-student/', agent_student_registration, name='agent_student_registration'),

    # Student Registration Portal Routes
    path('portal/register/', PortalStudentRegistrationView.as_view(), name='portal_student_registration'),
    path('portal/success/', portal_registration_success, name='portal_registration_success'),


    # SSW specific views
    path('aggredcs/', months_2026, name='contracts_2026'),

     path('student/<int:student_id>/pdf/', generate_student_pdf, name='generate_student_pdf'),
    
   

   
    
]