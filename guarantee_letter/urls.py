# guarantee_letter/urls.py
from django.urls import path
from . import views

app_name = 'guarantee_letter'

urlpatterns = [
    # ============ DASHBOARD ============
    path('', views.dashboard, name='dashboard'),
    
    # ============ LETTER MANAGEMENT ============
    # List letters
    path('letters/', views.letter_list, name='letter_list_list'),
    
    # Create new letter from template
    path('letters/create/', views.create_letter, name='create_letter'),
    
    # Upload existing PDF letter
    path('letters/upload/', views.upload_letter, name='upload_letter'),
    
    # Letter detail and actions
    path('letters/<int:pk>/', views.letter_detail, name='letter_detail'),
    path('letters/<int:pk>/edit/', views.edit_letter, name='edit_letter'),
    path('letters/<int:pk>/download/', views.download_letter, name='download_letter'),
    path('letters/<int:pk>/status/', views.update_status, name='update_status'),
    path('letters/<int:pk>/delete/', views.delete_letter, name='delete_letter'),
    
    # ============ CLIENT MANAGEMENT ============
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.add_client, name='add_client'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', views.edit_client, name='edit_client'),
    path('clients/<int:pk>/delete/', views.delete_client, name='delete_client'),
    
    # ============ TEMPLATE MANAGEMENT ============
    path('templates/', views.template_list, name='template_list'),
    path('templates/add/', views.add_template, name='add_template'),
    path('templates/<int:pk>/edit/', views.edit_template, name='edit_template'),
]