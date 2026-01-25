from django.urls import path
from .import views
app_name = 'coe_visa'


urlpatterns = [


 path('dashboard/', views.seoandvisa_dashboard, name='seoandvisa_dashboard'),
    path('update-coe/<int:student_id>/', views.update_coe_status, name='update_coe_status'),
    path('update-visa/<int:student_id>/', views.update_visa_status, name='update_visa_status'),
]