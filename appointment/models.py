from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class AppointmentSlot(models.Model):
    """Available time slots for appointments"""
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=1)
    booked_count = models.IntegerField(default=0)

    
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    @property
    def is_full(self):
        return self.booked_count >= self.max_capacity
    
    @property
    def formatted_date(self):
        return self.start_time.strftime("%Y-%m-%d")
    
    @property
    def formatted_time(self):
        return self.start_time.strftime("%H:%M")
    
        # In models.py, add this method to AppointmentSlot class
@property
def get_duration(self):
    """Calculate duration in minutes"""
    if self.start_time and self.end_time:
        duration = self.end_time - self.start_time
        return int(duration.total_seconds() / 60)
    return 0

class Appointment(models.Model):
    """Appointment booking model"""
    APPOINTMENT_AIMS = [
        ('consultation', 'Consultation'),
        ('meeting', 'Business Meeting'),
        ('interview', 'Interview'),
        ('demo', 'Product Demo'),
        ('support', 'Technical Support'),
        ('other', 'Other'),
    ]
    
    # Personal Information
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17)
    address = models.TextField()
    
    # Professional Information
    company_name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    
    # Appointment Details
    appointment_aim = models.CharField(max_length=50, choices=APPOINTMENT_AIMS)
    message = models.TextField(blank=True)
    
    # Scheduling
    appointment_slot = models.ForeignKey(AppointmentSlot, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmation_code = models.CharField(max_length=20, unique=True)
    is_confirmed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.date} {self.time}"
    
    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            import uuid
            self.confirmation_code = str(uuid.uuid4())[:8].upper()
        
        # Update date and time from appointment slot
        if self.appointment_slot:
            self.date = self.appointment_slot.start_time.date()
            self.time = self.appointment_slot.start_time.time()
        
        super().save(*args, **kwargs)
        
        # Update slot booked count
        if self.appointment_slot:
            self.appointment_slot.booked_count = Appointment.objects.filter(
                appointment_slot=self.appointment_slot
            ).count()
            self.appointment_slot.save()