from django.urls import path
from . import views

urlpatterns = [




    path('agreements/', views.agreement_list, name='agreement_list'),
    path('agreements/create/', views.agreement_create, name='agreement_create'),
    path('agreements/<int:pk>/update/', views.agreement_update, name='agreement_update'),
    path('agreements/<int:pk>/delete/', views.agreement_delete, name='agreement_delete'),
    path('agreements/<int:year>/', views.agreement_by_year, name='agreement_by_year'),
    path('agreements/years/', views.year_buttons, name='year_buttons'),
]

