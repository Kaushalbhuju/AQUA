from django.urls import path
from . import views

urlpatterns = [
    path('staffssw/', views.staff_ssw_working_visa, name='staff_ssw_working_visa'),
    path('staffstud/', views.staff_student_visa, name='staff_student_visa'),

]