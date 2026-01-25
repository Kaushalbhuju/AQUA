from django.urls import path
from . import views

urlpatterns = [
    path('letters/', views.letter_list, name='letter_list'),
    path('letters/upload/', views.letter_upload, name='letter_upload'),
    path('letters/<int:pk>/', views.letter_detail, name='letter_details'),
    path('letters/<int:pk>/delete/', views.letter_delete, name='letter_delete'),
]