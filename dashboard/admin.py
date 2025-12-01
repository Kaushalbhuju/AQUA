# dashboard/admin.py
from django.contrib import admin
from .models import Student, EducationalHistory, WorkExperience, StudentDocument
from candidate_portal.models import Agent, Candidate


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['agent_code', 'name', 'email', 'pin_code', 'max_candidates', 'current_candidate_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['agent_code', 'name', 'email']
    readonly_fields = ['current_candidate_count', 'created_at', 'last_used']
    list_per_page = 20
    
    def get_readonly_fields(self, request, obj=None):
        """Make agent_code and pin_code readonly only when editing existing object"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ['agent_code', 'pin_code']
        return self.readonly_fields
    
    def get_fieldsets(self, request, obj=None):
        """Different fieldsets for add vs change views"""
        if obj:  # Editing existing agent
            fieldsets = (
                ('Agent Information', {
                    'fields': ('name', 'email', 'agent_code', 'pin_code')
                }),
                ('Settings', {
                    'fields': ('is_active', 'max_candidates', 'current_candidate_count')
                }),
                ('Timestamps', {
                    'fields': ('created_at', 'last_used'),
                    'classes': ('collapse',)
                })
            )
        else:  # Creating new agent
            fieldsets = (
                ('Agent Information', {
                    'fields': ('name', 'email', 'agent_code', 'pin_code')
                }),
                ('Settings', {
                    'fields': ('is_active', 'max_candidates')
                })
            )
        return fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """Add help text for manual code entry during creation"""
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Only when creating new agent
            form.base_fields['agent_code'].help_text = 'Leave blank to auto-generate or enter custom code'
            form.base_fields['pin_code'].help_text = 'Leave blank to auto-generate or enter custom PIN'
            # Make fields not required since they can be auto-generated
            form.base_fields['agent_code'].required = False
            form.base_fields['pin_code'].required = False
        return form


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'email', 'phone', 'agent', 'is_active', 'created_at']
    list_filter = ['agent', 'is_active', 'created_at']
    search_fields = ['student_id', 'first_name', 'last_name', 'email', 'agent__agent_code']
    readonly_fields = ['candidate_id', 'student_id', 'created_at', 'last_access']
    list_per_page = 20
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Agent Information', {
            'fields': ('agent', 'student_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_access'),
            'classes': ('collapse',)
        })
    )

# ... rest of your admin classes remain the same ...
class EducationalHistoryInline(admin.TabularInline):
    model = EducationalHistory
    extra = 1
    fields = ['pass_level', 'school_name', 'admission_year', 'graduation_year', 'enrolled_years']

class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 1
    fields = ['work_type', 'company_name', 'join_date', 'resign_date', 'working_years']

class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 1
    fields = ['document_type', 'document_file', 'uploaded_at']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'agent', 'email', 'phone', 'status', 'created_at']
    list_filter = ['status', 'gender', 'marital_status', 'created_at', 'agent']
    search_fields = ['student_id', 'full_name', 'email', 'agent__agent_code']
    readonly_fields = ['student_id', 'created_at', 'updated_at']
    list_per_page = 20
    inlines = [EducationalHistoryInline, WorkExperienceInline, StudentDocumentInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'student_id', 'full_name', 'date_of_birth', 'age', 'gender', 
                'marital_status', 'photo'
            )
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'permanent_address', 'present_address')
        }),
        ('Passport Information', {
            'fields': (
                'passport_no', 'passport_issue_date', 'passport_expiry_date'
            ),
            'classes': ('collapse',)
        }),
        ('Physical Information', {
            'fields': ('height', 'weight', 'blood_group', 'medical_report', 'tb_status'),
            'classes': ('collapse',)
        }),
        ('Visa Information', {
            'fields': ('visa_apply_record', 'visa_details'),
            'classes': ('collapse',)
        }),
        ('Family Records', {
            'fields': ('spouse_name', 'spouse_contact'),
            'classes': ('collapse',)
        }),
        ('Certificates & Skills', {
            'fields': (
                'certificate_pass_year', 'certificate_name', 
                'language_join_year', 'organization',
                'driving_license', 'license_pass_year', 'license_discretion',
                'hobbies', 'motivation'
            ),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('agent', 'candidate')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_at', 'review_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EducationalHistory)
class EducationalHistoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'pass_level', 'school_name', 'admission_year', 'graduation_year', 'enrolled_years']
    list_filter = ['pass_level']
    search_fields = ['student__full_name', 'school_name']
    list_per_page = 20

@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['student', 'company_name', 'work_type', 'working_years']
    search_fields = ['student__full_name', 'company_name']
    list_per_page = 20

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'document_type', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['student__full_name']
    list_per_page = 20