# sswadmission/urls.py - COMPLETE VERSION
from django.urls import path
from . import views

app_name = 'sswdashboard'

urlpatterns = [
    # Dashboard
    path('', views.professional_dashboard, name='professional_dashboard'),
    path('quick-payment/', views.process_quick_payment, name='process_quick_payment'),
    
    # Student Management
    path('students/', views.student_list, name='student_list'),
    path('students/register/', views.student_registration, name='student_registration'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/<int:student_id>/update/', views.update_student, name='update_student'),
    path('students/<int:student_id>/status/', views.change_student_status, name='change_student_status'),
    
    # Payment Management
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/add/<int:student_id>/', views.add_payment, name='add_payment_for_student'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/verify/', views.verify_payment, name='verify_payment'),
    path('payments/<int:payment_id>/receipt/', views.generate_receipt, name='generate_receipt'),
    path('payments/verification/', views.payment_verification_queue, name='payment_verification_queue'),
    
    # Installment Management
    path('students/<int:student_id>/installments/create/', views.create_installments, name='create_installments'),
    path('installments/<int:installment_id>/paid/', views.mark_installment_paid, name='mark_installment_paid'),
    
    # Reports
    path('reports/financial/', views.financial_reports, name='financial_reports'),
    path('reports/admission-stats/', views.admission_statistics, name='admission_statistics'),
    
    # AJAX Endpoints
    path('ajax/metrics/', views.ajax_dashboard_metrics, name='ajax_dashboard_metrics'),
    path('ajax/chart-data/', views.ajax_payment_chart_data, name='ajax_payment_chart_data'),
    path('ajax/student-stats/', views.ajax_student_stats, name='ajax_student_stats'),
]