from django.contrib import admin
from .models import College, CollegeYearlyData

class CollegeYearlyDataInline(admin.TabularInline):
    model = CollegeYearlyData
    extra = 10
    max_num = 10

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ['college_id', 'college_name_english', 'phone_no', 'email', 'agreement_date', 'expire_date']
    list_filter = ['agreement_type', 'agreement_date']
    search_fields = ['college_id', 'college_name_english', 'college_name_japanese', 'email']
    inlines = [CollegeYearlyDataInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'college_id', 
                'college_name_english', 
                'college_name_japanese',
                'college_type'
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

@admin.register(CollegeYearlyData)
class CollegeYearlyDataAdmin(admin.ModelAdmin):
    list_display = ['college', 'year', 'yearly_student_no', 'interview_attend_no', 'interview_pass_no', 'visa_application_no', 'ceo_success_no']
    list_filter = ['year']
    search_fields = ['college__college_id', 'college__college_name_english']