# guarantee_letter/models.py - EXACT MATCH TO DATABASE
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date
import os
import uuid

def upload_to(instance, filename):
    """Generate unique file path for PDF uploads"""
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return f'guarantee_letters/{instance.candidate_name}/{unique_filename}'

class Client(models.Model):
    """Client model - EXACT MATCH to database"""
    name = models.CharField(max_length=100)  # Note: max_length=100 (not 200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    passport_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)  # Note: date_created (not created_at)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class JobGuaranteeLetterTemplate(models.Model):
    """Template for creating new job guarantee letters"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class JobGuaranteeLetter(models.Model):
    """Main model for Job Guarantee Letters - EXACT MATCH to database"""
    
    SOURCE_CHOICES = [
        ('uploaded', 'Uploaded PDF'),
        ('created', 'Created from Template'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('archived', 'Archived'),
    ]
    
    LETTER_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
    ]
    
    # Letter Identification
    letter_number = models.CharField(max_length=50, unique=True, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='created')
    
    # Client Information
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='letters')
    
    # Candidate Information
    candidate_name = models.CharField(max_length=200)
    candidate_email = models.EmailField()
    candidate_phone = models.CharField(max_length=20, blank=True)
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Job Details
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=100, blank=True)
    letter_type = models.CharField(max_length=20, choices=LETTER_TYPE_CHOICES, default='full_time')
    
    # Dates
    issue_date = models.DateField(default=date.today)
    start_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    
    # Salary Information
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_currency = models.CharField(max_length=10, default='USD', blank=True)
    
    # For UPLOAD source
    pdf_file = models.FileField(upload_to=upload_to, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    
    # For CREATE source
    template = models.ForeignKey(JobGuaranteeLetterTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    generated_content = models.TextField(blank=True)
    generated_pdf = models.FileField(upload_to='generated_letters/', blank=True, null=True)
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_confirmed = models.BooleanField(default=False)
    confirmation_date = models.DateField(blank=True, null=True)
    
    # User Information
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='issued_guarantee_letters')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='uploaded_guarantee_letters')
    
    # Additional Information
    remarks = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    content = models.TextField(blank=True)  # This exists in your database!
    
    # Timestamps
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.letter_number} - {self.candidate_name}"
    
    def save(self, *args, **kwargs):
        """Generate unique letter number if not exists"""
        if not self.letter_number:
            prefix = "UPL" if self.source == 'uploaded' else "CRT"
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.letter_number = f"{prefix}-{timestamp}"
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if letter is expired"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

class LetterLog(models.Model):
    """Audit log for letter actions"""
    ACTION_CHOICES = [
        ('upload', 'Uploaded'),
        ('create', 'Created'),
        ('verify', 'Verified'),
        ('reject', 'Rejected'),
        ('update', 'Updated'),
        ('download', 'Downloaded'),
        ('delete', 'Deleted'),
    ]
    
    letter = models.ForeignKey(JobGuaranteeLetter, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"{self.letter.letter_number} - {self.action} by {self.user.username}"
        return f"{self.letter.letter_number} - {self.action}"