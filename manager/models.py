
from django.db import models
from django.core.validators import RegexValidator

class StaffRegistration(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
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
    
    # Basic Information
    staff_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    full_name = models.CharField(max_length=200)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    permanent_address = models.TextField()
    present_address = models.TextField()
    candidate_photo = models.ImageField(upload_to='staff_photos/', null=True, blank=True)
    
    # ID/Passport Information
    id_passport_no = models.CharField(max_length=50)
    date_of_issue = models.DateField()
    issue_from = models.CharField(max_length=100)
    
    # Personal Information
    date_of_birth = models.DateField()
    eye_lense_right = models.CharField(max_length=20)
    eye_lense_left = models.CharField(max_length=20)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    phone_no = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Phone number must be exactly 10 digits.')]
    )
    email_id = models.EmailField()
    
    # Family Records
    spouse_name = models.CharField(max_length=200, blank=True)
    contact_no = models.CharField(max_length=20, blank=True)
    
    # Additional Information
    hobbies = models.TextField()
    motivation = models.TextField()
    
    #datapdf

    staff_bio_data_pdf = models.FileField(
        upload_to='staff_documents/bio_data/', 
        help_text='Upload Staff Bio Data PDF'
    )
    staff_id_doc_pdf = models.FileField(
        upload_to='staff_documents/id_docs/', 
        help_text='Upload Staff ID Document PDF'
    )
    staff_login_report_pdf = models.FileField(
        upload_to='staff_documents/login_reports/', 
        null=True, 
        blank=True,
        help_text='Upload Staff Login Report PDF'
    )
    staff_login_id_pdf = models.FileField(
        upload_to='staff_documents/login_ids/', 
        null=True, 
        blank=True,
        help_text='Upload Staff Login ID PDF'
    )
    
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Staff Registration'
        verbose_name_plural = 'Staff Registrations'
    
    def save(self, *args, **kwargs):
        if not self.staff_id:
            # Finding the first available ID to fill gaps
            existing_ids = set(StaffRegistration.objects.values_list('staff_id', flat=True))
            counter = 1
            while f"{counter:03d}" in existing_ids:
                counter += 1
            self.staff_id = f"{counter:03d}"
        super(StaffRegistration, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff_id} - {self.full_name}"
    

class BankInformation(models.Model):
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE, related_name='bank_info')
 
    bank_name = models.CharField(max_length=150)
    branch_name = models.CharField(max_length=150)
    account_no = models.CharField(max_length=50)
    account_holder_name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.bank_name} - {self.account_holder_name}"

class EducationalHistory(models.Model):
    PASS_LEVEL_CHOICES = [
        ('Primary', 'Primary School'),
        ('Junior', 'Junior H School'),
        ('Higher', 'Higher S School'),
        ('College', 'College / University'),
        ('Graduate', 'Graduate University'),
        ('PostGraduate', 'Post Graduate University'),
        ('Other', 'Other School'),
    ]
    
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE, related_name='education_history')
    pass_level = models.CharField(max_length=20, choices=PASS_LEVEL_CHOICES, )
    name_of_school = models.CharField(max_length=300)
    admission_year = models.IntegerField(null=True, blank=True)
    admission_month = models.IntegerField(null=True, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    graduation_month = models.IntegerField(null=True, blank=True)
    enrolled_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    class Meta:
        ordering = ['pass_level']
        verbose_name = 'Educational History'
        verbose_name_plural = 'Educational Histories'
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.pass_level}"


class WorkingExperience(models.Model):
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE, related_name='work_experience')
    type_of_work = models.CharField(max_length=200)
    name_of_company = models.CharField(max_length=300)
    join_year = models.IntegerField(null=True, blank=True)
    join_month = models.IntegerField(null=True, blank=True)
    resign_year = models.IntegerField(null=True, blank=True)
    resign_month = models.IntegerField(null=True, blank=True)
    working_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    class Meta:
        ordering = ['-join_year']
        verbose_name = 'Working Experience'
        verbose_name_plural = 'Working Experiences'
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.name_of_company}"


class CertificateOfSkills(models.Model):
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE, related_name='certificates')
    pass_year = models.IntegerField(null=True, blank=True)
    pass_month = models.IntegerField(null=True, blank=True)
    name_of_certificate = models.CharField(max_length=300)
    join_year = models.IntegerField(null=True, blank=True)
    join_month = models.IntegerField(null=True, blank=True)
    organization = models.CharField(max_length=300)
    
    class Meta:
        ordering = ['-pass_year']
        verbose_name = 'Certificate of Skills'
        verbose_name_plural = 'Certificates of Skills'
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.name_of_certificate}"


class SkillsTrainingStatus(models.Model):
    staff = models.ForeignKey(StaffRegistration, on_delete=models.CASCADE, related_name='training_status')
    pass_year = models.IntegerField(null=True, blank=True)
    pass_month = models.IntegerField(null=True, blank=True)
    name_of_training = models.CharField(max_length=300)
    join_year = models.IntegerField(null=True, blank=True)
    join_month = models.IntegerField(null=True, blank=True)
    organization = models.CharField(max_length=300)
    
    class Meta:
        ordering = ['-pass_year']
        verbose_name = 'Skills Training Status'
        verbose_name_plural = 'Skills Training Statuses'
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.name_of_training}"


class DrivingLicense(models.Model):
    staff = models.OneToOneField(StaffRegistration, on_delete=models.CASCADE, related_name='driving_license')
    pass_year = models.IntegerField(null=True, blank=True)
    pass_month = models.IntegerField(null=True, blank=True)
    discretion_of_license = models.CharField(max_length=500, blank=True)
    
    class Meta:
        verbose_name = 'Driving License'
        verbose_name_plural = 'Driving Licenses'
    
    def __str__(self):
        return f"{self.staff.full_name} - License"