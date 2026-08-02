from django.urls import path
from . import views

app_name = 'japanese_exam'

urlpatterns = [
    path('', views.exam_selection, name='exam_selection'),
    path('skill/', views.skill_exam_student_list, name='skill_exam_student_list'),
    path('<str:exam_type>/record/', views.record_exam_attempt, name='record_exam_attempt'),
    path('<str:exam_type>/export-excel/', views.export_exam_excel, name='export_exam_excel'),
    path('attempt/<int:result_id>/edit/', views.edit_exam_attempt, name='edit_exam_attempt'),
    path('attempt/<int:result_id>/delete/', views.delete_exam_attempt, name='delete_exam_attempt'),
    path('<str:exam_type>/', views.exam_student_list, name='exam_student_list'),
]
