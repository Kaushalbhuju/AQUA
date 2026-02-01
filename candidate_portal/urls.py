from django.urls import path
from . import views

app_name = 'candidate_portal'

urlpatterns = [
    # Agent authentication and portal access
    path('login/', views.AgentLoginView.as_view(), name='agent_login'),
    path('logout/', views.agent_logout, name='agent_logout'),
    path('success/', views.registration_success, name='registration_success'),
    
    # Agent Dashboard
    path('dashboard/', views.AgentDashboardView.as_view(), name='dashboard'),
    path('dashboardagent/', views.AgentDashboardView.as_view(), name='agent_dashboard'),
    
    # Registration
    path('register/', views.PortalStudentRegistrationView.as_view(), name='register_student'),
]