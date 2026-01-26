from django.db import models
from django.core.exceptions import ValidationError
import uuid
import random
import string

class Agent(models.Model):
    """Agent model"""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    agent_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    pin_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    max_candidates = models.PositiveIntegerField(default=100)
    current_candidate_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.agent_code})"

    def save(self, *args, **kwargs):
        if not self.agent_code:
            self.agent_code = self.generate_agent_code()
        if not self.pin_code:
            self.pin_code = self.generate_pin_code()
        super().save(*args, **kwargs)

    def can_register_candidate(self):
        return self.is_active and self.current_candidate_count < self.max_candidates

    def increment_candidate_count(self):
        if self.can_register_candidate():
            self.current_candidate_count += 1
            self.save(update_fields=['current_candidate_count', 'last_used'])
            return True
        return False

    @classmethod
    def generate_agent_code(cls):
        while True:
            code = f"AGT{random.randint(100000, 999999)}"
            if not cls.objects.filter(agent_code=code).exists():
                return code

    @classmethod
    def generate_pin_code(cls):
        while True:
            pin = ''.join(random.choices(string.digits, k=6))
            if not cls.objects.filter(pin_code=pin).exists():
                return pin

    class Meta:
        db_table = 'agents'
        ordering = ['-created_at']


class Contract(models.Model):
    """Agent contract with start and end dates"""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='contracts')
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"Contract for {self.agent.name} ({self.start_date} - {self.end_date})"

    class Meta:
        db_table = 'contracts'
        ordering = ['-start_date']


class Candidate(models.Model):
    """Candidate model"""
    candidate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='candidates')
    student_id = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = self.generate_student_id()
        super().save(*args, **kwargs)
        # Update agent's candidate count
        if not kwargs.get('update_fields'):
            self.agent.current_candidate_count = Candidate.objects.filter(agent=self.agent).count()
            self.agent.save(update_fields=['current_candidate_count'])

    def generate_student_id(self):
        agent_code = self.agent.agent_code
        last_candidate = Candidate.objects.filter(agent=self.agent).order_by('-created_at').first()
        
        if last_candidate and last_candidate.student_id:
            try:
                last_number = int(last_candidate.student_id.replace(agent_code, ''))
                next_number = last_number + 1
            except:
                next_number = 1
        else:
            next_number = 1
            
        return f"{agent_code}{next_number:04d}"

    class Meta:
        db_table = 'candidates'
        ordering = ['-created_at']