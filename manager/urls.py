from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('create/', views.staff_registration_create, name='staff_create'),
    path('<int:pk>/', views.staff_detail, name='staff_detail'),
    path('<int:pk>/update/', views.staff_registration_update, name='staff_update'),
    path('<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    path('mdashboard/', views.ssw_working_visa, name='ssw_working_visa'),
    path('mdashboardone/', views.student_visa, name='student_visa'),

]