from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('create/', views.staff_registration_create, name='staff_create'),
    path('join-us/', views.staff_self_registration, name='staff_self_register'),
    path('<int:pk>/', views.staff_detail, name='staff_detail'),
    path('<int:pk>/update/', views.staff_registration_update, name='staff_update'),
    path('<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    path('<int:pk>/print/', views.generate_staff_registration_pdf, name='staff_print_pdf'),
    path('staff-tasks/', views.manage_tasks, name='manage_tasks'),
    path('staff-activity/', views.staff_activity_log, name='staff_activity_log'),
    path('staff-activity/export/', views.staff_activity_export_csv, name='staff_activity_export_csv'),
    path('staff-attendance/', views.staff_attendance, name='staff_attendance'),
    path('staff-attendance/export/excel/', views.staff_attendance_export_excel, name='staff_attendance_export_excel'),
    path('language-skill-exam/', views.language_skill_dashboard, name='language_skill_dashboard'),
    path('mdashboard/', views.ssw_working_visa, name='ssw_working_visa'),
    path('mdashboardone/', views.student_visa, name='student_visa'),
    path('scan-documents/', views.scan_documents, name='scan_documents'),
    path('scan-documents/images-to-pdf/', views.images_to_pdf, name='images_to_pdf'),
    path('scan-documents/delete/<int:doc_id>/', views.delete_scanned_document, name='delete_scanned_document'),
    path('scan-documents/download/<int:doc_id>/', views.download_document, name='download_document'),
]
