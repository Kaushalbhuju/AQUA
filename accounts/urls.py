from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_view'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
]