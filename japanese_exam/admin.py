from django.contrib import admin
from .models import ExamResult, SkillExamResult

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam_type', 'status', 'score', 'recorded_by', 'created_at']
    list_filter = ['exam_type', 'status']
    search_fields = ['student__full_name', 'student__student_id']

@admin.register(SkillExamResult)
class SkillExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'skill_category', 'status', 'score', 'recorded_by', 'created_at']
    list_filter = ['skill_category', 'status']
    search_fields = ['student__full_name', 'student__student_id']
