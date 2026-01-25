# other_documents/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import os
import uuid
from datetime import datetime

def get_upload_path(instance, filename):
    """Generate a unique file path for uploaded documents"""
    # Simple path for now - we'll improve later
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return f'financial_docs/{instance.document_type}/{unique_filename}'

class FinancialDocument(models.Model):
    DOCUMENT_TYPES = [
        ('audit', 'Audit Report'),
        ('tax', 'Tax Filing'),
        ('financial', 'Financial Statement'),
        ('contract', 'Contract/Agreement'),
        ('invoice', 'Invoice/Receipt'),
        ('compliance', 'Compliance Document'),
        ('miscellaneous', 'Miscellaneous'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    # Basic fields - start simple
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to=get_upload_path)
    
    # User and timestamp
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Additional info
    fiscal_year = models.IntegerField(default=datetime.now().year)
    is_confidential = models.BooleanField(default=False)
    client_name = models.CharField(max_length=200, blank=True)
    project_code = models.CharField(max_length=50, blank=True)
    
    # Technical fields
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Financial Document"
        verbose_name_plural = "Financial Documents"
    
    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"
    
    def save(self, *args, **kwargs):
        # Set original filename on first save
        if not self.pk and self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0

class DocumentComment(models.Model):
    """Comments/notes on documents"""
    document = models.ForeignKey(FinancialDocument, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user} on {self.document.title}"