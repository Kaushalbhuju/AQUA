from django.contrib import admin
from .models import JobDemandLetter

class JobDemandLetterAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'uploaded_at')
    search_fields = ('title', 'description')
    list_filter = ('uploaded_at', 'uploaded_by')
    ordering = ('-uploaded_at',)
