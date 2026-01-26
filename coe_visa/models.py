# coe_visa/models.py
from django.db import models

class COETracking(models.Model):
    COE_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected'),
    ]
    
    student = models.OneToOneField(
        'dashboard.Student',  # String reference to Student in dashboards app
        on_delete=models.CASCADE, 
        related_name='coe_tracking'
    )
    status = models.CharField(max_length=20, choices=COE_STATUS_CHOICES, default='not_started')
    coe_number = models.CharField(max_length=50, blank=True, null=True)
    applied_date = models.DateField(null=True, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if hasattr(self, 'student'):
            return f"COE - {self.student.full_name}"
        return "COE - No Student"
    
    class Meta:
        ordering = ['-created_at']

class VisaTracking(models.Model):
    VISA_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('applied', 'Applied'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('stamped', 'Stamped'),
    ]
    
    student = models.OneToOneField(
        'dashboard.Student',  # String reference to Student in dashboards app
        on_delete=models.CASCADE, 
        related_name='visa_tracking'
    )
    status = models.CharField(max_length=20, choices=VISA_STATUS_CHOICES, default='not_started')
    application_number = models.CharField(max_length=50, blank=True, null=True)
    applied_date = models.DateField(null=True, blank=True)
    approved_date = models.DateField(null=True, blank=True)
    interview_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    visa_document = models.FileField(upload_to='visa_documents/', blank=True, null=True)
    
    # Departure Details
    ticket_file = models.FileField(upload_to='ticket_files/', blank=True, null=True)
    departure_airport = models.CharField(max_length=100, blank=True, null=True)
    transit_airport = models.CharField(max_length=100, blank=True, null=True)
    arrival_airport = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if hasattr(self, 'student'):
            return f"Visa - {self.student.full_name}"
        return "Visa - No Student"
    
    class Meta:
        ordering = ['-created_at']