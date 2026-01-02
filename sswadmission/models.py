# sswadmission/models.py - Complete Student model with FIXES
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
from django.db.models import Sum

class Student(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('enrolled', 'Enrolled'),
        ('graduated', 'Graduated'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    student_id = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    blood_group = models.CharField(max_length=5, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Nepal')
    pincode = models.CharField(max_length=10, blank=True)
    
    # Academic Information
    course = models.CharField(max_length=255, blank=True)
    batch = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    previous_institution = models.CharField(max_length=300, blank=True)
    
    # Admission Information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registration_date = models.DateField(default=timezone.now)
    admission_date = models.DateField(null=True, blank=True)
    
    # Fee Information
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    
    # Additional Information
    remarks = models.TextField(blank=True)
    
    # System Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_students'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate student ID if not provided
        if not self.student_id:
            year = timezone.now().strftime('%Y')
            # Get the last student ID
            last_student = Student.objects.order_by('-id').first()
            if last_student and last_student.student_id:
                try:
                    # Extract number from existing ID
                    last_num = int(last_student.student_id[-4:]) if last_student.student_id[-4:].isdigit() else 0
                except:
                    last_num = 0
            else:
                last_num = 0
            
            self.student_id = f"SSW{year[-2:]}{last_num + 1:04d}"
        
        # Calculate due amount
        effective_fee = self.total_fee - self.discount
        self.due_amount = effective_fee - self.paid_amount
        
        # Ensure due amount is not negative
        if self.due_amount < 0:
            self.due_amount = Decimal('0')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student_id} - {self.full_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def fee_paid_percentage(self):
        effective_fee = self.total_fee - self.discount
        if effective_fee > 0:
            return (self.paid_amount / effective_fee) * 100
        return 0
    
    def update_payment_status(self):
        """Update paid_amount from payments"""
        total_paid = self.fee_payments.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        self.paid_amount = total_paid
        effective_fee = self.total_fee - self.discount
        self.due_amount = effective_fee - total_paid
        
        if self.due_amount < 0:
            self.due_amount = Decimal('0')
        
        self.save(update_fields=['paid_amount', 'due_amount'])
    
    def get_payment_status_display(self):
        if self.due_amount <= 0 and self.total_fee > 0:
            return 'fully_paid'
        elif self.paid_amount == 0 and self.total_fee > 0:
            return 'not_paid'
        elif self.due_amount > 0:
            return 'partially_paid'
        else:
            return 'no_fee_set'

class FeePayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('online_payment', 'Online Payment'),
        ('cheque', 'Cheque'),
        ('card', 'Credit/Debit Card'),
        ('upi', 'Wallet'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    payment_id = models.CharField(max_length=50, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='completed')
    
    # Transaction Details
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True)
    cheque_number = models.CharField(max_length=50, blank=True)
    cheque_date = models.DateField(null=True, blank=True)
    utr_number = models.CharField(max_length=100, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)
    
    # Receipt Information
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Description
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # System Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def save(self, *args, **kwargs):
        # Generate payment ID if not exists
        if not self.payment_id:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = uuid.uuid4().hex[:6].upper()
            self.payment_id = f"PAY-{timestamp}-{random_str}"
        
        # Generate receipt number if not exists
        if not self.receipt_number:
            year = timezone.now().strftime('%y')
            last_payment = FeePayment.objects.order_by('-id').first()
            last_num = last_payment.id if last_payment else 0
            self.receipt_number = f"RCPT/{year}/{last_num + 1:06d}"
        
        super().save(*args, **kwargs)
        
        # Update student's payment status
        if self.student and (self.status == 'completed' or self.status == 'refunded'):
            self.student.update_payment_status()
    
    def __str__(self):
        return f"{self.payment_id} - {self.student.student_id} - ₹{self.amount}"

class FeeInstallment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['installment_number']
        unique_together = ['student', 'installment_number']
    
    def __str__(self):
        return f"Installment {self.installment_number} - {self.student.student_id}"
    
    @property
    def is_overdue(self):
        if self.status == 'pending' and self.due_date < timezone.now().date():
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Auto-update status if overdue
        if self.status == 'pending' and self.due_date < timezone.now().date():
            self.status = 'overdue'
        super().save(*args, **kwargs)