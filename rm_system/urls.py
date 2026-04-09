from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.admin_site import custom_admin_site
from django.http import FileResponse, Http404
import os


def serve_media(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404("File not found.")
    response = FileResponse(open(full_path, 'rb'))
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.pdf',):
        response['Content-Type'] = 'application/pdf'
    elif ext in ('.png',):
        response['Content-Type'] = 'image/png'
    elif ext in ('.jpg', '.jpeg'):
        response['Content-Type'] = 'image/jpeg'
    elif ext in ('.docx',):
        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return response


# Register all models with the custom admin site
from accounts.admin import UserAdmin
from accounts.models import User
from dashboard.admin import StudentAdmin, EducationalHistoryAdmin, WorkExperienceAdmin, StudentDocumentAdmin, AgentAdmin
from dashboard.models import Student, EducationalHistory, WorkExperience, StudentDocument, Agent

# Import models defensively
try:
    from company.admin import CollegeAdmin
    from company.models import College
    company_available = True
except ImportError:
    company_available = False

try:
    from staff.admin import StaffAdmin
    from staff.models import Staff
    staff_available = True
except ImportError:
    staff_available = False

try:
    from appointment.admin import AppointmentAdmin
    from appointment.models import Appointment
    appointment_available = True
except ImportError:
    appointment_available = False

try:
    from sswadmission.admin import StudentAdmin as SSWStudentAdmin, FeePaymentAdmin, FeeInstallmentAdmin
    from sswadmission.models import Student as SSWStudent, FeePayment, FeeInstallment
    sswadmission_available = True
except ImportError:
    sswadmission_available = False

try:
    from guarantee_letter.admin import GuaranteeLetterAdmin
    from guarantee_letter.models import GuaranteeLetter
    guarantee_letter_available = True
except ImportError:
    guarantee_letter_available = False

try:
    from coe_visa.admin import COEVisaAdmin
    from coe_visa.models import COEVisa
    coe_visa_available = True
except ImportError:
    coe_visa_available = False

try:
    from other_documents.admin import OtherDocumentAdmin
    from other_documents.models import OtherDocument
    other_documents_available = True
except ImportError:
    other_documents_available = False

try:
    from regcompany.admin import CompanyAdmin, CompanyYearlyDataAdmin
    from regcompany.models import Company, CompanyYearlyData
    regcompany_available = True
except ImportError:
    regcompany_available = False

try:
    from manager.admin import StaffRegistrationAdmin
    from manager.models import StaffRegistration
    manager_available = True
except ImportError:
    manager_available = False

try:
    from candidate_portal.admin import ContractAdmin
    from candidate_portal.models import Contract
    candidate_portal_available = True
except ImportError:
    candidate_portal_available = False

try:
    # Assuming Document and DocumentAdmin are in sswdash
    from sswdash.admin import DocumentAdmin
    from sswdash.models import Document
    sswdash_available = True
except ImportError:
    sswdash_available = False

try:
    from agreementdocx.admin import AgreementAdmin
    from agreementdocx.models import Agreement
    agreementdocx_available = True
except ImportError:
    agreementdocx_available = False

try:
    from jobd_letter.admin import JobDemandLetterAdmin
    from jobd_letter.models import JobDemandLetter
    jobd_letter_available = True
except ImportError:
    jobd_letter_available = False

try:
    from books.admin import BookAdmin
    from books.models import Book
    books_available = True
except ImportError:
    books_available = False

# Unregister from default admin if registered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Register models with custom admin site
try:
    custom_admin_site.register(User, UserAdmin)
except admin.sites.AlreadyRegistered:
    pass

try:
    custom_admin_site.register(Student, StudentAdmin)
except admin.sites.AlreadyRegistered:
    pass

try:
    custom_admin_site.register(EducationalHistory, EducationalHistoryAdmin)
except admin.sites.AlreadyRegistered:
    pass

try:
    custom_admin_site.register(WorkExperience, WorkExperienceAdmin)
except admin.sites.AlreadyRegistered:
    pass

try:
    custom_admin_site.register(StudentDocument, StudentDocumentAdmin)
except admin.sites.AlreadyRegistered:
    pass

try:
    custom_admin_site.register(Agent, AgentAdmin)
except admin.sites.AlreadyRegistered:
    pass

if company_available:
    try:
        custom_admin_site.register(College, CollegeAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if staff_available:
    try:
        custom_admin_site.register(Staff, StaffAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if manager_available:
    try:
        custom_admin_site.register(StaffRegistration, StaffRegistrationAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if appointment_available:
    try:
        custom_admin_site.register(Appointment, AppointmentAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if sswadmission_available:
    try:
        custom_admin_site.register(SSWStudent, SSWStudentAdmin)
    except admin.sites.AlreadyRegistered:
        pass
    try:
        custom_admin_site.register(FeePayment, FeePaymentAdmin)
    except admin.sites.AlreadyRegistered:
        pass
    try:
        custom_admin_site.register(FeeInstallment, FeeInstallmentAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if guarantee_letter_available:
    try:
        custom_admin_site.register(GuaranteeLetter, GuaranteeLetterAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if coe_visa_available:
    try:
        custom_admin_site.register(COEVisa, COEVisaAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if other_documents_available:
    try:
        custom_admin_site.register(OtherDocument, OtherDocumentAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if regcompany_available:
    try:
        custom_admin_site.register(Company, CompanyAdmin)
    except admin.sites.AlreadyRegistered:
        pass
    try:
        custom_admin_site.register(CompanyYearlyData, CompanyYearlyDataAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if candidate_portal_available:
    try:
        custom_admin_site.register(Contract, ContractAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if sswdash_available:
    try:
        custom_admin_site.register(Document, DocumentAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if agreementdocx_available:
    try:
        custom_admin_site.register(Agreement, AgreementAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if jobd_letter_available:
    try:
        custom_admin_site.register(JobDemandLetter, JobDemandLetterAdmin)
    except admin.sites.AlreadyRegistered:
        pass

if books_available:
    try:
        custom_admin_site.register(Book, BookAdmin)
    except admin.sites.AlreadyRegistered:
        pass

urlpatterns = [
    path('admin/', custom_admin_site.urls),
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
    path('books/', include('books.urls', namespace='books')),

]

# Media files - served via custom view (works in both DEBUG and production)
urlpatterns += [
    path('media/<path:path>', serve_media, name='serve_media'),
]

# Static files - served by Django in DEBUG, by WhiteNoise in production
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Fallback static file serving for production (when WhiteNoise isn't working)
if not settings.DEBUG:
    def serve_static(request, path):
        from django.http import FileResponse, Http404
        import os
        from django.conf import settings
        full_path = os.path.join(settings.STATIC_ROOT, path)
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise Http404("Static file not found.")
        return FileResponse(open(full_path, 'rb'))
    
    urlpatterns += [
        path('static/<path:path>', serve_static, name='serve_static'),
    ]
