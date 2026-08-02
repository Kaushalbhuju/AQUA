from django.urls import path
from translation import views

app_name = 'translation'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Document management
    path('upload/', views.document_upload, name='document_upload'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/process/', views.document_process, name='document_process'),
    path('documents/<int:pk>/review/', views.document_review, name='document_review'),
    path('documents/<int:pk>/complete/', views.document_complete, name='document_complete'),
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('documents/<int:pk>/bilingual-pdf/', views.document_bilingual_pdf, name='document_bilingual_pdf'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),

    # Translation Memory
    path('memory/', views.tm_list, name='tm_list'),
    path('memory/add/', views.tm_add, name='tm_add'),
    path('memory/<int:pk>/edit/', views.tm_edit, name='tm_edit'),
    path('memory/<int:pk>/delete/', views.tm_delete, name='tm_delete'),
    path('memory/clear/', views.tm_clear, name='tm_clear'),

    # History
    path('history/', views.history_list, name='history_list'),

    # Utilities
    path('seed-types/', views.seed_types, name='seed_types'),
]
