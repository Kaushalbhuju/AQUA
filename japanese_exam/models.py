from django.db import models
from django.conf import settings
from dashboard.models import Student

class ExamResult(models.Model):
    EXAM_TYPE_CHOICES = [
        ('JFT', 'JFT Exam'),
        ('JLPT', 'JLPT Exam'),
    ]
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    exam_type = models.CharField(max_length=4, choices=EXAM_TYPE_CHOICES)
    status = models.CharField(max_length=4, choices=STATUS_CHOICES, blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'exam_type')

    def __str__(self):
        return f"{self.student.full_name} - {self.exam_type} - {self.status or 'Pending'}"


class SkillExamResult(models.Model):
    SKILL_CATEGORY_CHOICES = [
        ('caregiving', 'Caregiving: Long-term Care Specified Skilled Worker Evaluation Test'),
        ('agriculture', 'Agriculture: Agriculture Skill Assessment Test (Crop and Livestock)'),
        ('food_services', 'Food Services: Food Service Industry Skill Test'),
        ('food_beverage', 'Food & Beverage: Food and Beverage Manufacturing Industry Skill Test'),
        ('construction', 'Construction: Construction Field Evaluation Test'),
        ('accommodation', 'Accommodation: Accommodation Industry Proficiency Test'),
        ('automobile', 'Automobile: Automobile Repair and Maintenance Field Skill Test'),
        ('manufacturing', 'Manufacturing: Industrial Product Manufacturing Field (Machining, Electronics, Metal Processing)'),
        ('fishery_aquaculture', 'Fishery & Aquaculture: Fishing Industry Skills Proficiency Test'),
        ('building_cleaning', 'Building Cleaning: Building Cleaning Management Field Test'),
        ('others', 'Others: Shipbuilding, Aviation, Forestry, Wood Industry'),
    ]
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='skill_exam_results')
    skill_category = models.CharField(max_length=30, choices=SKILL_CATEGORY_CHOICES)
    status = models.CharField(max_length=4, choices=STATUS_CHOICES, blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'skill_category')

    def __str__(self):
        return f"{self.student.full_name} - {self.get_skill_category_display()} - {self.status or 'Pending'}"
