from django.contrib import admin
from .models import Appointment, AppointmentSlot

@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'is_available', 'booked_count', 'max_capacity', 'is_full')
    list_filter = ('is_available', 'start_time')
    search_fields = ('start_time',)
    date_hierarchy = 'start_time'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_name', 'date', 'time', 'appointment_aim', 'is_confirmed')
    list_filter = ('appointment_aim', 'is_confirmed', 'date')
    search_fields = ('name', 'email', 'company_name', 'confirmation_code')
    readonly_fields = ('confirmation_code', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone', 'address')
        }),
        ('Professional Information', {
            'fields': ('company_name', 'position')
        }),
        ('Appointment Details', {
            'fields': ('appointment_aim', 'message', 'appointment_slot', 'date', 'time')
        }),
        ('System Information', {
            'fields': ('confirmation_code', 'is_confirmed', 'created_at', 'updated_at')
        }),
    )