from django.contrib import admin
from .models import (
    StaffRegistration, EducationalHistory, WorkingExperience,
    CertificateOfSkills, SkillsTrainingStatus, DrivingLicense, ScannedDocument
)

class EducationalHistoryInline(admin.TabularInline):
    model = EducationalHistory
    extra = 1

class WorkingExperienceInline(admin.TabularInline):
    model = WorkingExperience
    extra = 1

class CertificateOfSkillsInline(admin.TabularInline):
    model = CertificateOfSkills
    extra = 1

class SkillsTrainingStatusInline(admin.TabularInline):
    model = SkillsTrainingStatus
    extra = 1

class DrivingLicenseInline(admin.StackedInline):
    model = DrivingLicense
    extra = 0

@admin.register(StaffRegistration)
class StaffRegistrationAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'full_name', 'gender', 'phone_no', 'email_id', 'created_at']
    list_filter = ['gender', 'marital_status', 'blood_group', 'created_at']
    search_fields = ['staff_id', 'full_name', 'email_id', 'phone_no']
    inlines = [
        EducationalHistoryInline,
        WorkingExperienceInline,
        CertificateOfSkillsInline,
        SkillsTrainingStatusInline,
        DrivingLicenseInline,
    ]


@admin.register(ScannedDocument)
class ScannedDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_name', 'document_type', 'candidate_name', 'uploaded_by', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['document_name', 'candidate_name', 'candidate_id']
    readonly_fields = ['created_at', 'uploaded_by']


admin.site.register(EducationalHistory)
admin.site.register(WorkingExperience)
admin.site.register(CertificateOfSkills)
admin.site.register(SkillsTrainingStatus)
admin.site.register(DrivingLicense)