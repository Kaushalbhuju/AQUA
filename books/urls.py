from django.urls import path
from books import views

app_name = 'books'

urlpatterns = [
    # IMPORTANT: Specific routes MUST come BEFORE <str:book_id>/ pattern!
    
    # Books - specific routes
    path('', views.book_list, name='book_list'),
    path('add/', views.book_create, name='book_create'),
    path('generate-all-qrs/', views.generate_all_qr, name='generate_all_qr'),
    path('generate-all-stickers/', views.generate_all_stickers, name='generate_all_stickers'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/add/', views.template_create, name='template_create'),
    path('templates/<int:template_id>/edit/', views.template_update, name='template_update'),
    path('templates/<int:template_id>/delete/', views.template_delete, name='template_delete'),
    
    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('scan/<str:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('scan/book/<str:book_id>/', views.scan_book, name='scan_book'),
    path('assignment/<str:assignment_id>/download/', views.download_assignment_pdf, name='download_assignment_pdf'),
    
    # Books - generic route (MUST be LAST)
    path('<str:book_id>/', views.book_detail, name='book_detail'),
    path('<str:book_id>/edit/', views.book_update, name='book_update'),
    path('<str:book_id>/delete/', views.book_delete, name='book_delete'),
    path('<str:book_id>/assign/', views.assign_book, name='assign_book'),
    path('<str:book_id>/return/', views.return_book, name='return_book'),
    path('<str:book_id>/qr/', views.qr_page, name='qr_page'),
]
