from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.AppointmentCreateView.as_view(), name='book_appointment'),
    path('slots/', views.AppointmentSlotListView.as_view(), name='available_slots'),
    path('api/slots/', views.get_available_slots_api, name='slots_api'),
    path('confirmation/', views.AppointmentConfirmationView.as_view(), name='appointment_confirmation'),
    path('test/', views.test, name='test_page'),
    path('', views.home_view, name='home'),
    path('test/', views.test_view, name='test_css'),
]