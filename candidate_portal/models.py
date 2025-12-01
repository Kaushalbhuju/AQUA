from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import random
import string

class Agent(models.Model):
    """Enhanced Agent model with unique identifier validation"""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    agent_code = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,  
        null=True,   # Allow blank for auto-generation
        help_text="Leave blank to auto-generate"
    )
    pin_code = models.CharField(
        max_length=10, 
        unique=True, 
        blank=True, 
        null=True,   # Allow blank for auto-generation
        help_text="Leave blank to auto-generate"
    )
    is_active = models.BooleanField(default=True)
    max_candidates = models.PositiveIntegerField(
        default=100, 
        help_text="Maximum candidates allowed for this agent"
    )
    current_candidate_count = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.agent_code})"
    
    def save(self, *args, **kwargs):
        """Auto-generate agent_code and pin_code if not provided"""
        if not self.agent_code:
            self.agent_code = self.generate_agent_code()
        if not self.pin_code:
            self.pin_code = self.generate_pin_code()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate agent data before saving"""
        # Ensure agent code is uppercase and alphanumeric
        if self.agent_code:
            self.agent_code = self.agent_code.upper().strip()
            if not self.agent_code.isalnum():
                raise ValidationError({'agent_code': 'Agent code must be alphanumeric.'})
    
    def can_register_candidate(self):
        """Check if agent can register more candidates"""
        return self.is_active and self.current_candidate_count < self.max_candidates
    
    def increment_candidate_count(self):
        """Safely increment candidate count"""
        if self.can_register_candidate():
            self.current_candidate_count += 1
            self.save(update_fields=['current_candidate_count', 'last_used'])
            return True
        return False
    
    def reset_candidate_count(self):
        """Reset candidate count (admin function)"""
        self.current_candidate_count = 0
        self.save(update_fields=['current_candidate_count'])
    
    @classmethod
    def generate_agent_code(cls):
        """Generate unique agent code: AGT + 6 digits"""
        while True:
            code = f"AGT{random.randint(100000, 999999)}"
            if not cls.objects.filter(agent_code=code).exists():
                return code
    
    @classmethod
    def generate_pin_code(cls):
        """Generate unique 6-digit pin code"""
        while True:
            pin = ''.join(random.choices(string.digits, k=6))
            if not cls.objects.filter(pin_code=pin).exists():
                return pin
    
    class Meta:
        db_table = 'agents'
        ordering = ['-created_at']


class Candidate(models.Model):
    """Enhanced Candidate model with unique student ID generation"""
    candidate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='candidates')
    
    # Student ID will be generated upon registration
    student_id = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_access = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"
    
    def clean(self):
        """Validate candidate data"""
        if not self.agent.can_register_candidate():
            raise ValidationError({
                'agent': f'Agent {self.agent.agent_code} has reached maximum candidate limit ({self.agent.max_candidates}).'
            })
        
        # Ensure email is unique per agent
        if Candidate.objects.filter(
            email=self.email, 
            agent=self.agent
        ).exclude(pk=self.pk).exists():
            raise ValidationError({'email': 'A candidate with this email already exists for this agent.'})
    
    def generate_student_id(self):
        """Generate unique student ID: AGENT_CODE + sequential number"""
        if self.student_id:
            return self.student_id  # Already generated
        
        # Get the next sequential number for this agent
        last_candidate = Candidate.objects.filter(
            agent=self.agent
        ).order_by('-created_at').first()
        
        if last_candidate and last_candidate.student_id:
            try:
                # Extract number from existing student ID
                last_number = int(last_candidate.student_id.replace(self.agent.agent_code, ''))
                next_number = last_number + 1
            except (ValueError, AttributeError):
                next_number = 1
        else:
            next_number = 1
        
        # Format: AGENT_CODE + 4-digit sequential number
        self.student_id = f"{self.agent.agent_code}{next_number:04d}"
        
        # Ensure uniqueness (handle race conditions)
        counter = 1
        original_id = self.student_id
        while Candidate.objects.filter(student_id=self.student_id).exists():
            self.student_id = f"{original_id}_{counter}"
            counter += 1
        
        return self.student_id
    
    def save(self, *args, **kwargs):
        """Override save to generate student ID and update agent count"""
        is_new = self.pk is None
        
        if is_new:
            # Generate student ID before saving
            self.generate_student_id()
        
        super().save(*args, **kwargs)
        
        if is_new:
            # Increment agent candidate count after successful save
            self.agent.increment_candidate_count()
    
    class Meta:
        db_table = 'candidates'
        unique_together = ['agent', 'email']
        ordering = ['-created_at']