from django.urls import path
from . import views

app_name = 'candidate_portal'

urlpatterns = [
    # Agent authentication and portal access
    # path('', views.AgentLoginView.as_view(), name='agent_login'),
    path('logout/', views.agent_logout, name='agent_logout'),
    path('success/', views.registration_success, name='registration_success'),
    
    # Legacy URLs for backward compatibility
    # path('legacy/', views.CandidateLoginView.as_view(), name='candidate_login_legacy'),
    # path('legacy/logout/', views.candidate_logout, name='candidate_logout_legacy'),
    # path('agent/<str:agent_code>/', views.AgentCandidatePageView.as_view(), name='agent_candidate_page_legacy'),
    #path('agentlogin/', views.AgentLoginView.as_view(), name='agent_candidate_login_legacy'),
    #path('', views.AgentLoginView.as_view(), name='agent_login'),
    path('logout/', views.agent_logout, name='agent_logout'),
    path('success/', views.registration_success, name='registration_success'),
    path('dashboardagent/', views.AgentDashboardView.as_view(), name='agent_dashboard'),
    
    # Legacy URLs for backward compatibility
    # path('legacy/', views.CandidateLoginView.as_view(), name='candidate_login_legacy'),
    # path('legacy/logout/', views.candidate_logout, name='candidate_logout_legacy'),
    # path('agent/<str:agent_code>/', views.AgentCandidatePageView.as_view(), name='agent_candidate_page_legacy'),

    path('login/', views.AgentLoginView.as_view(), name='agent_login'),
    path('logout/', views.agent_logout, name='agent_logout'),
    
    # Agent Dashboard
    path('dashboard/', views.AgentDashboardView.as_view(), name='dashboard'),
    
    # Registration
    path('register/', views.PortalStudentRegistrationView.as_view(), name='register_student'),
    path('success/', views.registration_success, name='registration_success'),
    path('login/', views.AgentLoginView.as_view(), name='agent_login'),
    path('logout/', views.agent_logout, name='agent_logout'),
    
    # Agent Dashboard
    path('dashboard/', views.AgentDashboardView.as_view(), name='agent_dashboard'),
    
    # Registration
    path('register/', views.PortalStudentRegistrationView.as_view(), name='register_student'),
    path('success/', views.registration_success, name='registration_success'),


    
]