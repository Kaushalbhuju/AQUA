from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('staffssw/', views.staff_ssw_working_visa, name='staff_ssw_working_visa'),
    path('staffstud/', views.staff_student_visa, name='staff_student_visa'),
    path('tasks/', views.my_tasks, name='my_tasks'),
    path('tasks/<int:task_id>/update/', views.update_task_status, name='update_task_status'),
]
