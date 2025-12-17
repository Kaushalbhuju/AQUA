# appointment/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ================ PUBLIC URLS ================
    path('', views.AppointmentSlotListView.as_view(), name='available_slots'),
    path('book/', views.AppointmentCreateView.as_view(), name='book_appointment'),
    path('confirmation/', views.AppointmentConfirmationView.as_view(), name='appointment_confirmation'),
    
    # Public appointment detail using confirmation code
    path('public/<str:confirmation_code>/', views.appointment_detail_public, name='appointment_detail_public'),
    
    # ================ ADMIN URLS ================
    # Admin dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Admin appointment management
    path('admin/appointments/', views.appointment_list, name='appointment_list'),
    path('admin/appointment/<int:pk>/', views.appointment_detail_admin, name='appointment_detail_admin'),
    path('admin/appointment/<int:appointment_id>/confirm/', views.confirm_appointment, name='confirm_appointment'),
    path('admin/appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    
    # ================ SLOT MANAGEMENT ================
    path('admin/slots/', views.slot_management, name='slot_management'),
    path('admin/slots/create/', views.create_slot, name='create_slot'),
    path('admin/slots/<int:pk>/edit/', views.edit_slot, name='edit_slot'),
    path('admin/slots/<int:pk>/delete/', views.delete_slot, name='delete_slot'),
    path('admin/slots/<int:pk>/toggle/', views.toggle_slot_availability, name='toggle_slot_availability'),
    
    # ================ EXPORT ================
    path('admin/export/appointments/', views.export_appointments, name='export_appointments'),
    path('admin/export/slots/', views.export_slots, name='export_slots'),
    
    # ================ REPORTS ================
    path('admin/reports/appointments/', views.appointment_report, name='appointment_report'),
]