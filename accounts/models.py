# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('operation_head', 'Operation Head'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('client', 'Recruitment Client'),
        ('college', 'College'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f"{self.username} ({self.role})"

    def get_dashboard_url(self):
        """
        Returns the appropriate dashboard URL based on the user's role.
        """
        role_to_url = {
            'operation_head': '/dashboard/operation_head/',
            'manager': '/dashboard/manager/',
            'staff': '/dashboard/staff/',
            'client': '/dashboard/recruitment_client/',
            'college': '/dashboard/college_student/',
        }
        return role_to_url.get(self.role, '/dashboard/')
