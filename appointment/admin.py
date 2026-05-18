from django.contrib import admin
from django.contrib import messages
from .models import Appointment, AppointmentSlot
from .emails import AppointmentEmailService


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'is_available', 'booked_count', 'max_capacity', 'is_full')
    list_filter = ('is_available', 'start_time')
    search_fields = ('start_time',)
    date_hierarchy = 'start_time'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'company_name', 'date', 'time', 
        'appointment_aim', 'is_confirmed', 'confirmation_code'
    )
    list_filter = ('appointment_aim', 'is_confirmed', 'date')
    search_fields = ('name', 'email', 'company_name', 'confirmation_code')
    readonly_fields = ('confirmation_code', 'created_at', 'updated_at')
    date_hierarchy = 'date'
    actions = ['confirm_selected_appointments']
    
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
    
    @admin.action(description='Confirm selected appointments and send emails')
    def confirm_selected_appointments(self, request, queryset):
        """
        Admin action to confirm multiple appointments at once.
        
        This action:
        1. Sets is_confirmed=True for each selected appointment
        2. Sends confirmation email to each user
        3. Reports success/failure counts
        
        Args:
            request: The current HttpRequest
            queryset: QuerySet of selected Appointment objects
        """
        confirmed_count = 0
        email_sent_count = 0
        already_confirmed = 0
        failed_emails = 0
        
        for appointment in queryset:
            if appointment.is_confirmed:
                already_confirmed += 1
                continue
            
            # Confirm the appointment
            appointment.is_confirmed = True
            appointment.save()
            confirmed_count += 1
            
            # Send confirmation email
            try:
                success = AppointmentEmailService.send_admin_confirmation(
                    appointment, request=request
                )
                if success:
                    email_sent_count += 1
                else:
                    failed_emails += 1
            except Exception as e:
                failed_emails += 1
                self.message_user(
                    request,
                    f"Failed to send email to {appointment.email}: {str(e)}",
                    level=messages.WARNING
                )
        
        # Report results
        if confirmed_count > 0:
            self.message_user(
                request,
                f"Successfully confirmed {confirmed_count} appointment(s). "
                f"Emails sent: {email_sent_count}.",
                level=messages.SUCCESS
            )
        
        if already_confirmed > 0:
            self.message_user(
                request,
                f"{already_confirmed} appointment(s) were already confirmed.",
                level=messages.WARNING
            )
        
        if failed_emails > 0:
            self.message_user(
                request,
                f"Failed to send {failed_emails} email(s). Check logs for details.",
                level=messages.ERROR
            )
