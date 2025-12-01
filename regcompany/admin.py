from django.contrib import admin
from .models import Company, CompanyYearlyData

class CompanyYearlyDataInline(admin.TabularInline):
    model = CompanyYearlyData
    extra = 5
    max_num = 10

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['company_id', 'company_name_english', 'phone_no', 'email', 'agreement_date', 'expire_date']
    list_filter = ['agreement_type', 'agreement_date']
    search_fields = ['company_id', 'company_name_english', 'company_name_japanese', 'email']
    inlines = [CompanyYearlyDataInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'company_id', 
                'company_name_english', 
                'company_name_japanese',
                'company_type'
            )
        }),
        ('Contact Information', {
            'fields': (
                'phone_no', 
                'fax_no', 
                'email', 
                'website'
            )
        }),
        ('Address Information', {
            'fields': (
                'head_office_address', 
                'corporate_office_address'
            )
        }),
        ('Representative Information', {
            'fields': (
                'representative_name', 
                'representative_mobile'
            )
        }),
        ('Agreement Information', {
            'fields': (
                'agreement_date', 
                'expire_date', 
                'agreement_type'
            )
        }),
        ('Documents', {
            'fields': (
                'agreement_doc',
                'interview_pass_doc',
                'visa_apply_doc',
                'ceo_visa_doc',
                'other_doc',
                'pdf_doc_1',
                'pdf_doc_2',
            ),
            'classes': ('collapse',)
        }),
    )

@admin.register(CompanyYearlyData)
class CompanyYearlyDataAdmin(admin.ModelAdmin):
    list_display = ['company', 'year', 'yearly_student_no', 'interview_attend_no', 'interview_pass_no', 'visa_application_no', 'ceo_success_no']
    list_filter = ['year']
    search_fields = ['company__company_id', 'company__company_name_english']