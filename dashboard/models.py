# models.py
from django.db import models
from candidate_portal.models import Agent, Candidate
import base64
import mimetypes

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
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    full_name = models.CharField(max_length=100)
    japanese_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Japanese Name (Katakana/Hiragana)')
    date_of_birth = models.DateField()
    photo = models.ImageField(upload_to='student_photos/')
    permanent_address = models.TextField()
    present_address = models.TextField(blank=True, null=True)
    age = models.IntegerField()
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    family_records = models.TextField(blank=True, null=True)
    
    # Passport Information
    passport_no = models.CharField(max_length=20, blank=True, null=True)
    passport_issue_date = models.DateField(blank=True, null=True)
    passport_expiry_date = models.DateField(blank=True, null=True)

    # Physical Information
    height = models.CharField(max_length=20)
    weight = models.CharField(max_length=20)
    eye_lens_right = models.CharField(max_length=50, verbose_name='Eye Lens - Right')
    eye_lens_left = models.CharField(max_length=50, verbose_name='Eye Lens - Left')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    tb_status = models.CharField(max_length=10)
    
    # Visa Information
    visa_apply_record = models.CharField(max_length=3, choices=VISA_CHOICES, blank=True, null=True)
    visa_details = models.TextField(blank=True, null=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=10)
    
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
    license_type_2 = models.CharField(max_length=100, blank=True, null=True)
    license_pass_year_2 = models.CharField(max_length=50, blank=True, null=True)
    hobbies = models.TextField(blank=False, null=True)
    motivation = models.TextField(blank=False, null=True)
    
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

    @property
    def photo_display_url(self):
        """Return a usable photo URL only if the file still exists."""
        if not self.photo:
            return None

        try:
            if self.photo.storage.exists(self.photo.name):
                return self.photo.url
        except Exception:
            return None

        return None

    @property
    def photo_data_uri(self):
        """Return the photo as a data URI so templates don't depend on media serving."""
        if not self.photo:
            return None

        try:
            with self.photo.open('rb') as image_file:
                encoded = base64.b64encode(image_file.read()).decode('ascii')
            mime_type = mimetypes.guess_type(self.photo.name)[0] or 'image/jpeg'
            return f'data:{mime_type};base64,{encoded}'
        except Exception:
            return None

    @property
    def calculated_age(self):
        """Calculate age from date_of_birth"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return self.age
    
    def generate_student_id(self):
        """Generate student ID based on agent code and highest existing numeric suffix"""
        if self.agent:
            # Get all students for this agent
            agent_students = Student.objects.filter(agent=self.agent)
            
            # Find the maximum numeric suffix from existing student IDs
            max_num = 0
            for s in agent_students:
                if s.student_id and '-' in s.student_id:
                    try:
                        num_part = s.student_id.split('-')[-1]
                        num = int(num_part)
                        if num > max_num:
                            max_num = num
                    except (ValueError, IndexError):
                        continue
            
            next_num = max_num + 1
            return f"{self.agent.agent_code}-{next_num:04d}"
        return None
    
    def save(self, *args, **kwargs):
        if not self.student_id and self.agent:
            self.student_id = self.generate_student_id()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


class Classroom(models.Model):
    """Model to represent a classroom/class group"""
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='classrooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def student_count(self):
        return self.class_students.count()


class ClassStudent(models.Model):
    """Model to link students to classrooms (roster)"""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='class_students')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='class_memberships')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['classroom', 'student']
        ordering = ['student__full_name']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.classroom.name}"


class AttendanceRecord(models.Model):
    """Model to store student attendance records"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
        ('holiday', 'Holiday'),
    ]
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='attendance_records')
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records')
    attendance_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'attendance_date', 'classroom']
        ordering = ['-attendance_date', '-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.attendance_date} ({self.status})"


class TeacherStudentRecord(models.Model):
    """List of students that a teacher has added to their records view"""
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='record_students')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='teacher_records')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['teacher', 'student']
        ordering = ['student__full_name']

    def __str__(self):
        return f"{self.teacher.username} - {self.student.full_name}"


class StudentDailyNote(models.Model):
    """Daily notes written by teachers for individual students"""
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='daily_notes')
    teacher = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='written_notes')
    note_date = models.DateField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'note_date', 'teacher']
        ordering = ['-note_date', '-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.note_date}"
    
    @property
    def is_editable(self):
        """Note is editable only within 24 hours of creation"""
        from django.utils import timezone
        if not self.created_at:
            return True
        return (timezone.now() - self.created_at).total_seconds() < 86400  # 24 hours


class EducationalHistory(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='education_history')
    pass_level = models.CharField(max_length=50)
    school_name = models.CharField(max_length=200)
    admission_year = models.IntegerField(blank=True, null=True)
    admission_month = models.CharField(max_length=20, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    graduation_month = models.CharField(max_length=20, blank=True, null=True)
    enrolled_years = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.pass_level}"

class WorkExperience(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='work_experience')
    work_type = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200)
    join_date = models.CharField(max_length=50, blank=True, null=True)
    resign_date = models.CharField(max_length=50, blank=True, null=True)
    working_years = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.company_name}"

class StudentDocument(models.Model):
    DOCUMENT_TYPES = [
        ('bio_data', 'Passport'),
        ('id_info', 'Citizenship/Driving'),
        ('educational_doc', 'Graduation/Transcript'),
        ('report', 'Medical Report'),
        ('other', 'Other PDF'),
    ]
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='student_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.get_document_type_display()}"

    def document_file_url(self):
        if self.document_file and self.document_file.name:
            from django.conf import settings
            if settings.DEBUG:
                return self.document_file.url
            return f"/media/{self.document_file.name}"
        return None

  # Add get_display methods
    def get_gender_display(self):
        return dict(self._meta.get_field('gender').choices).get(self.gender, self.gender)
    
    def get_marital_status_display(self):
        return dict(self._meta.get_field('marital_status').choices).get(self.marital_status, self.marital_status)
