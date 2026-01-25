from django.contrib import admin

# Register your models here.
# coe_visa/admin.py
from django.contrib import admin
from .models import COETracking, VisaTracking

@admin.register(COETracking)
class COETrackingAdmin(admin.ModelAdmin):
    list_display = ['student', 'status', 'coe_number', 'applied_date', 'issued_date']
    list_filter = ['status']
    search_fields = ['student__full_name', 'student__student_id', 'coe_number']

@admin.register(VisaTracking)
class VisaTrackingAdmin(admin.ModelAdmin):
    list_display = ['student', 'status', 'application_number', 'applied_date', 'approved_date']
    list_filter = ['status']
    search_fields = ['student__full_name', 'student__student_id', 'application_number']