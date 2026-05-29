from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from dashboard.models import Student
from .models import ExamResult, SkillExamResult

@login_required
def exam_selection(request):
    return render(request, 'japanese_exam/exam_selection.html')

@login_required
def exam_student_list(request, exam_type):
    if exam_type not in ['JFT', 'JLPT']:
        messages.error(request, 'Invalid exam type.')
        return redirect('japanese_exam:exam_selection')

    students = Student.objects.filter(status='approved').order_by('full_name')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        status_val = request.POST.get('status')
        score_val = request.POST.get('score')

        if student_id and status_val:
            student = get_object_or_404(Student, id=student_id, status='approved')
            ExamResult.objects.update_or_create(
                student=student,
                exam_type=exam_type,
                defaults={
                    'status': status_val,
                    'score': int(score_val) if score_val else None,
                    'recorded_by': request.user,
                }
            )
            messages.success(request, f'Result recorded for {student.full_name}')
        return redirect('japanese_exam:exam_student_list', exam_type=exam_type)

    results_map = {
        r.student_id: r
        for r in ExamResult.objects.filter(exam_type=exam_type).select_related('student')
    }

    student_data = []
    for s in students:
        result = results_map.get(s.id)
        student_data.append({
            'student': s,
            'result': result,
        })

    return render(request, 'japanese_exam/exam_student_list.html', {
        'student_data': student_data,
        'exam_type': exam_type,
    })


@login_required
def skill_exam_student_list(request):
    students = Student.objects.filter(status='approved').order_by('full_name')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        skill_category = request.POST.get('skill_category')
        status_val = request.POST.get('status')
        score_val = request.POST.get('score')

        if student_id and skill_category and status_val:
            student = get_object_or_404(Student, id=student_id, status='approved')
            SkillExamResult.objects.update_or_create(
                student=student,
                skill_category=skill_category,
                defaults={
                    'status': status_val,
                    'score': int(score_val) if score_val else None,
                    'recorded_by': request.user,
                }
            )
            messages.success(request, f'Skill result recorded for {student.full_name}')
        return redirect('japanese_exam:skill_exam_student_list')

    results_map = {
        r.student_id: r
        for r in SkillExamResult.objects.all().select_related('student')
    }

    student_data = []
    for s in students:
        result = results_map.get(s.id)
        student_data.append({
            'student': s,
            'result': result,
        })

    return render(request, 'japanese_exam/skill_exam_student_list.html', {
        'student_data': student_data,
        'skill_categories': SkillExamResult.SKILL_CATEGORY_CHOICES,
    })
