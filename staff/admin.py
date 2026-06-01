from django.contrib import admin
from .models import StaffTask

@admin.register(StaffTask)
class StaffTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'assigned_by', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['title', 'assigned_to__username']
