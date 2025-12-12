from django.urls import path
from . import views
app_name = 'sswdash'

urlpatterns = [
    path('upload/', views.upload_document, name='upload_document'),
    path('documents/', views.list_documents, name='list_documents'),
    path('documents/delete/<int:pk>/', views.delete_document, name='delete_document'),
]
