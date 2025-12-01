from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Aqua Admin"
admin.site.site_title = "Aqua Admin Portal"
admin.site.index_title = "Welcome to Operation Head Portal"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Account-related URLs
    path('', include('accounts.urls')),        # Includes ALL accounts URLs
    path('register/', include('accounts.urls')),
    
    # Other app URLsA
    path('dashboard/', include('dashboard.urls')),
    path('manager/', include('manager.urls')),
    path('company/', include('company.urls')),
    path('regcompany/', include('regcompany.urls')),
    path('portal/', include('candidate_portal.urls')),
    path('staff/', include('staff.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
