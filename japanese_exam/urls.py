from django.urls import path
from . import views

app_name = 'japanese_exam'

urlpatterns = [
    path('', views.exam_selection, name='exam_selection'),
    path('skill/', views.skill_exam_student_list, name='skill_exam_student_list'),
    path('<str:exam_type>/', views.exam_student_list, name='exam_student_list'),
]
