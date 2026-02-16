# sswadmission/admin.py - COMPLETE VERSION
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import Student, FeePayment, FeeInstallment
from django.db.models import Sum

# Custom Admin Actions
@admin.action(description="Approve selected students")
def approve_selected_students(modeladmin, request, queryset):
    updated = queryset.update(status='approved', updated_at=timezone.now())
    messages.success(request, f'{updated} student(s) approved!')

@admin.action(description="Mark as enrolled")
def mark_as_enrolled(modeladmin, request, queryset):
    updated = queryset.update(status='enrolled', updated_at=timezone.now())
    messages.success(request, f'{updated} student(s) marked as enrolled!')

@admin.action(description="Mark payment as completed")
def mark_payment_completed(modeladmin, request, queryset):
    for payment in queryset:
        payment.status = 'completed'
        payment.verified_by = request.user
        payment.verified_at = timezone.now()
        payment.save()
    messages.success(request, f'{queryset.count()} payment(s) marked as completed!')

@admin.action(description="Mark payment as failed")
def mark_payment_failed(modeladmin, request, queryset):
    updated = queryset.update(status='failed', updated_at=timezone.now())
    messages.success(request, f'{updated} payment(s) marked as failed!')

# Inline Admin
class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    readonly_fields = ['payment_id', 'receipt_number', 'created_at', 'payment_status_display']
    fields = ['payment_id', 'amount', 'payment_method', 'payment_status_display', 'payment_date', 'status']
    can_delete = False
    
    def payment_status_display(self, obj):
        color = {'pending': 'orange', 'completed': 'green', 'failed': 'red', 'refunded': 'blue'}.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    payment_status_display.short_description = 'Status'

class FeeInstallmentInline(admin.TabularInline):
    model = FeeInstallment
    extra = 0
    readonly_fields = ['status_display']
    fields = ['installment_number', 'amount', 'due_date', 'status_display', 'paid_date']
    can_delete = False
    
    def status_display(self, obj):
        color = {'pending': 'orange', 'paid': 'green', 'overdue': 'red', 'cancelled': 'gray'}.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    status_display.short_description = 'Status'

# Student Admin
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'course', 'status_display', 'fee_display', 'payment_status', 'created_at']
    list_filter = ['status', 'course', 'registration_date', 'gender']
    search_fields = ['student_id', 'full_name', 'email', 'phone', 'course']
    readonly_fields = ['student_id', 'created_at', 'updated_at', 'due_amount', 'created_by', 'age_display', 'fee_paid_percentage_display']
    inlines = [FeePaymentInline, FeeInstallmentInline]
    actions = [approve_selected_students, mark_as_enrolled]
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('student_id', 'full_name', 'email', 'phone', 'date_of_birth', 'gender', 'blood_group', 'age_display')
        }),
        ('Academic Info', {
            'fields': ('course', 'batch', 'qualification', 'previous_institution', 'status', 'registration_date', 'admission_date')
        }),
        ('Fee Information', {
            'fields': ('total_fee', 'discount', 'paid_amount', 'due_amount', 'fee_paid_percentage_display')
        }),
        ('Address & Contact', {
            'fields': ('address', 'city', 'state', 'country', 'pincode', 'emergency_contact_name', 'emergency_contact'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('remarks', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def status_display(self, obj):
        color = {'pending': 'orange', 'approved': 'blue', 'enrolled': 'green', 'declined': 'red', 'graduated': 'purple'}.get(obj.status, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_display.short_description = 'Status'
    
    def fee_display(self, obj):
        effective_fee = obj.total_fee - obj.discount
        if effective_fee == 0:
            return format_html('<span style="color: gray;">No Fee</span>')
        
        percentage = (obj.paid_amount / effective_fee) * 100 if effective_fee > 0 else 0
        color = 'green' if percentage >= 100 else 'orange' if percentage > 0 else 'red'
        return format_html('₹{} / ₹{} <small>({}%)</small>', 
                          obj.paid_amount, effective_fee, int(percentage))
    fee_display.short_description = 'Fee Paid'
    
    def payment_status(self, obj):
        status = obj.get_payment_status_display()
        colors = {
            'fully_paid': 'green',
            'partially_paid': 'orange',
            'not_paid': 'red',
            'no_fee_set': 'gray'
        }
        status_text = {
            'fully_paid': 'Paid',
            'partially_paid': 'Partial',
            'not_paid': 'Unpaid',
            'no_fee_set': 'No Fee'
        }
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                          colors.get(status, 'gray'), status_text.get(status, status))
    payment_status.short_description = 'Payment'
    
    def age_display(self, obj):
        return obj.age if obj.age else 'N/A'
    age_display.short_description = 'Age'
    
    def fee_paid_percentage_display(self, obj):
        percentage = obj.fee_paid_percentage
        color = 'green' if percentage >= 100 else 'orange' if percentage >= 50 else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, int(percentage))
    fee_paid_percentage_display.short_description = 'Payment Progress'

# Fee Payment Admin
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'student_link', 'amount_display', 'payment_method_display', 
                   'status_display', 'payment_date', 'verified_info']
    list_filter = ['status', 'payment_method', 'payment_date', 'verified_at']
    search_fields = ['payment_id', 'receipt_number', 'student__student_id', 
                    'student__full_name', 'transaction_id']
    readonly_fields = ['payment_id', 'receipt_number', 'created_at', 'updated_at', 
                      'created_by', 'verified_by', 'verified_at']
    actions = [mark_payment_completed, mark_payment_failed]
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('payment_id', 'student', 'amount', 'payment_date', 'payment_method', 'status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'bank_name', 'cheque_number', 'cheque_date', 'utr_number', 'upi_id'),
            'classes': ('collapse',)
        }),
        ('Receipt & Description', {
            'fields': ('receipt_number', 'description', 'notes')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_link(self, obj):
        url = reverse('admin:sswadmission_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}<br><small>{}</small></a>', 
                          url, obj.student.full_name, obj.student.student_id)
    student_link.short_description = 'Student'
    
    def amount_display(self, obj):
        return format_html('<strong>₹{}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()
    payment_method_display.short_description = 'Method'
    
    def status_display(self, obj):
        color = {'pending': 'orange', 'completed': 'green', 'failed': 'red', 'refunded': 'blue'}.get(obj.status, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_display.short_description = 'Status'
    
    def verified_info(self, obj):
        if obj.verified_by and obj.verified_at:
            return format_html('{}<br><small>{}</small>', 
                              obj.verified_by.username, 
                              obj.verified_at.strftime('%Y-%m-%d %H:%M'))
        return format_html('<span style="color: orange;">Pending</span>')
    verified_info.short_description = 'Verified'

# Fee Installment Admin
class FeeInstallmentAdmin(admin.ModelAdmin):
    list_display = ['student_link', 'installment_number', 'amount_display', 'due_date', 
                   'status_display', 'paid_date', 'is_overdue_display']
    list_filter = ['status', 'due_date', 'student__course']
    search_fields = ['student__student_id', 'student__full_name', 'notes']
    
    def student_link(self, obj):
        url = reverse('admin:sswadmission_student_change', args=[obj.student.id])
        return format_html('<a href="{}">{}<br><small>{}</small></a>', 
                          url, obj.student.full_name, obj.student.student_id)
    student_link.short_description = 'Student'
    
    def amount_display(self, obj):
        return format_html('₹{}', obj.amount)
    amount_display.short_description = 'Amount'
    
    def status_display(self, obj):
        color = {'pending': 'orange', 'paid': 'green', 'overdue': 'red', 'cancelled': 'gray'}.get(obj.status, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_status_display())
    status_display.short_description = 'Status'
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Overdue</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    is_overdue_display.short_description = 'Overdue Status'