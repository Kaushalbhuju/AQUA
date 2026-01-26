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
    
    # Account URLs - ONLY ONCE
    path('', include('accounts.urls')),
    
    # Agent Portal URLs - All agent functionality here
    path('agent/', include('candidate_portal.urls', namespace='agent_portal')),
    
    # Other app URLs
    path('dashboard/', include('dashboard.urls')),
    path('manager/', include('manager.urls')),
    path('company/', include('company.urls')),
    path('regcompany/', include('regcompany.urls')),
    path('staff/', include('staff.urls')),
    path('sswdash/', include('sswdash.urls')),
    path('sswadmission/', include('sswadmission.urls')),
    path('appointment/', include('appointment.urls')),
    path('candidate/', include('candidate_portal.urls')),
    path('', include('jobd_letter.urls')),
    path('agreementdocx/', include('agreementdocx.urls')),
    path('documents/', include('guarantee_letter.urls')),
    path('coe-visa/', include('coe_visa.urls')),
    path('other-documents/', include('other_documents.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    