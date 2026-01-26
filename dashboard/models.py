# models.py
from django.db import models
from candidate_portal.models import Agent, Candidate

class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    VISA_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    
    # Pipeline Stages
    STAGE_CHOICES = [
        ('candidate_info', 'Candidate Information'),
        ('select_candidate', 'Select Candidate'),
        ('interview_pattern', 'Interview Pattern'),
        ('pass_interview', 'Pass Interview'),
        ('ceo_approval', 'CEO Approval'),
        ('visa_arrival', 'Visa & Arrival'),
        ('completed', 'Completed'),
    ]
    
    # Approval Status
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='candidate_info')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    
    # Connection with Candidate Portal
    candidate = models.OneToOneField(
        Candidate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='student'
    )
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='students'
    )
    
    # Personal Information
    student_id = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    full_name = models.CharField(max_length=100, default='Unknown Student')
    date_of_birth = models.DateField(default='2000-01-01')
    photo = models.ImageField(upload_to='student_photos/', null=False, blank=False, default='student_photos/default.png')
    permanent_address = models.TextField(default='Unknown')
    present_address = models.TextField(blank=True, null=True)
    age = models.IntegerField(default=18)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, default='single')
    
    # Passport Information
    passport_no = models.CharField(max_length=20, blank=False, null=False, default='UNKNOWN')
    passport_issue_date = models.DateField(blank=False, null=False, default='2000-01-01')
    passport_expiry_date = models.DateField(blank=False, null=False, default='2030-01-01')
    
    # Physical Information
    height = models.CharField(max_length=20, blank=False, null=False, default='0')
    weight = models.CharField(max_length=20, blank=False, null=False, default='0')
    medical_report =models.FileField(upload_to='medical_reports/', null=True, blank=True)
    eye_lens_right = models.CharField(max_length=50, blank=False, null=False, verbose_name='Eye Lens - Right', default='Normal')
    eye_lens_left = models.CharField(max_length=50, blank=False, null=False, verbose_name='Eye Lens - Left', default='Normal')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=False, null=False, default='O+')
    tb_status = models.CharField(max_length=10, blank=False, null=False, default='negative')
    
    # Visa Information
    visa_apply_record = models.CharField(max_length=3, choices=VISA_CHOICES, blank=True, null=True)
    visa_details = models.TextField(blank=True, null=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    
    # Family Records
    spouse_name = models.CharField(max_length=100, blank=True, null=True)
    spouse_contact = models.CharField(max_length=15, blank=True, null=True)
    
    # Certificates & Skills
    certificate_pass_year = models.CharField(max_length=50, blank=True, null=True)
    certificate_name = models.CharField(max_length=200, blank=True, null=True)
    language_join_year = models.CharField(max_length=50, blank=True, null=True)
    organization = models.CharField(max_length=200, blank=True, null=True)
    driving_license = models.CharField(max_length=100, blank=True, null=True)
    license_pass_year = models.CharField(max_length=50, blank=True, null=True)
    license_discretion = models.TextField(blank=True, null=True)
    hobbies = models.TextField(blank=True, null=True)
    motivation = models.TextField(blank=True, null=True)
    
    # Additional fields for pipeline stages
    qualification = models.CharField(max_length=100, blank=True, null=True)
    experience = models.IntegerField(default=0)
    interview_date = models.DateField(null=True, blank=True)
    interview_type = models.CharField(max_length=50, blank=True, null=True)
    interviewer_name = models.CharField(max_length=100, blank=True, null=True)
    interview_score = models.IntegerField(null=True, blank=True)
    interview_feedback = models.TextField(blank=True, null=True)
    ceo_approval_status = models.CharField(max_length=50, blank=True, null=True)
    ceo_approval_date = models.DateField(null=True, blank=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    visa_status = models.CharField(max_length=50, blank=True, null=True)
    expected_arrival = models.DateField(null=True, blank=True)
    accommodation_status = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student_id} - {self.full_name}"
    
    def generate_student_id(self):
        """Generate student ID based on agent code"""
        if self.agent:
            student_count = Student.objects.filter(agent=self.agent).count() + 1
            return f"{self.agent.agent_code}-{student_count:04d}"
        return None
    
    def save(self, *args, **kwargs):
        if not self.student_id and self.agent:
            self.student_id = self.generate_student_id()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']

class EducationalHistory(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='education_history')
    pass_level = models.CharField(max_length=50)
    school_name = models.CharField(max_length=200)
    admission_year = models.IntegerField(blank=True, null=True)
    admission_month = models.CharField(max_length=20, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    graduation_month = models.CharField(max_length=20, blank=True, null=True)
    enrolled_years = models.IntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.pass_level}"

class WorkExperience(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='work_experience')
    work_type = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200)
    join_date = models.CharField(max_length=50, blank=True, null=True)
    resign_date = models.CharField(max_length=50, blank=True, null=True)
    working_years = models.IntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.company_name}"

class StudentDocument(models.Model):
    DOCUMENT_TYPES = [
        ('bio_data', 'Student BIO-DATA'),
        ('id_info', 'Student ID Information'),
        ('educational_doc', 'Student Educational Doc'),
        ('report', 'Student Report'),
        ('other', 'PDF'),
    ]
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='student_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.get_document_type_display()}"
    
 # Add get_display methods
    def get_gender_display(self):
        return dict(self._meta.get_field('gender').choices).get(self.gender, self.gender)
    
    def get_marital_status_display(self):
        return dict(self._meta.get_field('marital_status').choices).get(self.marital_status, self.marital_status)