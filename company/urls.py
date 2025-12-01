from django.urls import path
from . import views

app_name = 'company'

urlpatterns = [
    path('colleges/', views.CollegeListView.as_view(), name='college_list'),
    path('colleges/create/', views.CollegeCreateView.as_view(), name='college_create'),
    path('colleges/<int:pk>/', views.CollegeDetailView.as_view(), name='college_detail'),
    path('colleges/<int:pk>/update/', views.CollegeUpdateView.as_view(), name='college_update'),
    path('dashboard/', views.college_dashboard, name='college_dashboard'),
]