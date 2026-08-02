from django.contrib.admin import AdminSite
from accounts.models import User
from dashboard.models import Student
try:
    from company.models import Company
except ImportError:
    Company = None

class CustomAdminSite(AdminSite):
    site_header = "AQUA Education Admin"
    site_title = "AQUA Education Admin Portal"
    index_title = "Welcome to AQUA Education Admin Dashboard"

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_list = super().get_app_list(request)

        # Add custom ordering
        app_ordering = {
            'accounts': 1,         
            'dashboard': 2,
            'company': 3,
            'staff': 4,
            'appointment': 5,
            'sswadmission': 6,
            'guarantee_letter': 7,
            'coe_visa': 8,
            'other_documents': 9,
            'agreementdocx': 10,
            'jobd_letter': 11,
            'translation': 12,
        }

        for app in app_list:
            app['order'] = app_ordering.get(app['app_label'], 99)

        app_list.sort(key=lambda x: x['order'])
        return app_list

    def index(self, request, extra_context=None):
        """
        Display the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        # Get statistics for dashboard
        user_count = User.objects.count()
        student_count = Student.objects.count()
        company_count = Company.objects.count() if Company else 0
        pending_count = Student.objects.filter(status='pending').count()

        extra_context = extra_context or {}
        extra_context.update({
            'user_count': user_count,
            'student_count': student_count,
            'company_count': company_count,
            'pending_count': pending_count,
            'django_version': '5.2.7',
            'debug': True,  # In production, this should be settings.DEBUG
        })

        return super().index(request, extra_context)

# Create the custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')
