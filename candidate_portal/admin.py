# candidate_portal/admin.py
from django.contrib import admin
from .models import Contract

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    
    list_display = ('agent', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('agent__name', 'agent__email')
