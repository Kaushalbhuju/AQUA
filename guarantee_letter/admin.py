# guarantee_letter/admin.py - UPDATED
from django.contrib import admin
from .models import Client, JobGuaranteeLetter, JobGuaranteeLetterTemplate, LetterLog

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'passport_number', 'phone', 'date_created']
    search_fields = ['name', 'email', 'passport_number', 'phone']
    ordering = ['name']

@admin.register(JobGuaranteeLetterTemplate)
class JobGuaranteeLetterTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_by', 'date_created']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(JobGuaranteeLetter)
class JobGuaranteeLetterAdmin(admin.ModelAdmin):
    list_display = ['letter_number', 'candidate_name', 'client', 'job_title', 'source', 'status', 'issue_date']
    list_filter = ['source', 'status', 'letter_type', 'issue_date', 'client']
    search_fields = ['letter_number', 'candidate_name', 'candidate_email', 'passport_number', 'job_title']
    readonly_fields = ['date_created', 'date_updated']
    ordering = ['-issue_date']

@admin.register(LetterLog)
class LetterLogAdmin(admin.ModelAdmin):
    list_display = ['letter', 'action', 'user', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['letter__letter_number', 'user__username', 'details']
    readonly_fields = ['letter', 'action', 'user', 'details', 'created_at']
    ordering = ['-created_at']