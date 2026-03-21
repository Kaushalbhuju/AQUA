# dashboard_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.urls import reverse
from dashboard.models import Student
from dashboard.decorators import check_role




@login_required(login_url='login')
@check_role('operation_head')
def operation_head_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'Operation Head', 
        'role_description': 'Manage overall operations and staff'
    }
    return render(request, 'dashboards/operation_head_dashboard.html', context)

@login_required(login_url='login')
@check_role('manager')
def manager_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'Manager', 
        'role_description': 'Manage team and projects'
    }
    return render(request, 'dashboards/manager_dashboard.html', context)

@login_required(login_url='login')
@check_role('staff')
def staff_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'Staff', 
        'role_description': 'View assigned tasks and updates'
    }
    return render(request, 'dashboards/staff_dashboard.html', context)

@login_required(login_url='login')
@check_role('college')
def college_student_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'College Student', 
        'role_description': 'View job opportunities and apply for positions'
    }
    return render(request, 'dashboards/college_student_dashboard.html', context)

@login_required(login_url='login')
@check_role('teacher')
def teacher_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'Teacher', 
        'role_description': 'Manage student attendance and records'
    }
    return render(request, 'dashboards/teacher_dashboard.html', context)

@login_required(login_url='login')
@check_role('teacher')
def student_attendance(request):
    """Redirect to class list for class-based attendance"""
    return redirect('dashboard:class_list')


@login_required(login_url='login')
@check_role('teacher')
def class_list(request):
    """View showing all classes for the teacher"""
    from dashboard.models import Classroom
    classrooms = Classroom.objects.all()
    
    # Auto-create 4 default classes if none exist
    if not classrooms.exists():
        for name in ['Class A', 'Class B', 'Class C', 'Class D']:
            Classroom.objects.create(name=name, teacher=request.user)
        classrooms = Classroom.objects.all()
    
    context = {
        'user': request.user,
        'role_name': 'Teacher',
        'classrooms': classrooms,
        'page_title': 'Student Attendance'
    }
    return render(request, 'dashboards/class_list.html', context)


@login_required(login_url='login')
@check_role('teacher')
def class_attendance(request, classroom_id):
    """View for marking attendance inside a class"""
    from dashboard.models import Classroom, ClassStudent, AttendanceRecord
    import calendar
    from datetime import date
    
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    class_students = ClassStudent.objects.filter(classroom=classroom).select_related('student')
    students = [cs.student for cs in class_students]
    
    # Get month/year from query params (default: current month)
    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if month < 1 or month > 12:
            month = today.month
    except (ValueError, TypeError):
        year = today.year
        month = today.month
    
    days_in_month = calendar.monthrange(year, month)[1]
    month_name = calendar.month_name[month]
    days = list(range(1, days_in_month + 1))
    
    # Compute prev/next month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    # Build attendance matrix
    student_data = []
    for student in students:
        records = AttendanceRecord.objects.filter(
            student=student,
            classroom=classroom,
            attendance_date__year=year,
            attendance_date__month=month
        )
        attendance_map = {r.attendance_date.day: r.status for r in records}
        
        day_statuses = []
        present_count = 0
        holiday_count = 0
        for day in days:
            status = attendance_map.get(day, '')  # empty = not marked
            day_statuses.append(status)
            if status == 'present':
                present_count += 1
            elif status == 'holiday':
                holiday_count += 1
        
        effective_days = days_in_month - holiday_count
        percentage = round((present_count / effective_days) * 100) if effective_days > 0 else 0
        
        student_data.append({
            'student': student,
            'day_statuses': day_statuses,
            'present_count': present_count,
            'percentage': percentage,
        })
    
    context = {
        'user': request.user,
        'classroom': classroom,
        'student_data': student_data,
        'days': days,
        'month_name': month_name,
        'year': year,
        'month': month,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'page_title': f'Attendance - {classroom.name}',
    }
    return render(request, 'dashboards/class_attendance.html', context)


@login_required(login_url='login')
@check_role('teacher')
def save_class_attendance(request, classroom_id):
    """AJAX endpoint to save O/X attendance for a class"""
    from django.http import JsonResponse
    from dashboard.models import Classroom, ClassStudent, AttendanceRecord, Student
    import json
    from datetime import date
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        classroom = get_object_or_404(Classroom, pk=classroom_id)
        data = json.loads(request.body)
        records = data.get('records', [])
        
        saved_count = 0
        for rec in records:
            student_id = rec.get('studentId')
            day = rec.get('day')
            status = rec.get('status')  # 'present' or 'absent'
            japanese_name = rec.get('japaneseName', None)
            
            try:
                student = Student.objects.get(id=student_id)
                
                # Update Japanese name if provided
                if japanese_name is not None:
                    student.japanese_name = japanese_name
                    student.save()
                
                # Build the date
                year = data.get('year', date.today().year)
                month = data.get('month', date.today().month)
                att_date = date(year, month, day)
                if status in ('present', 'absent', 'holiday'):
                    attendance, created = AttendanceRecord.objects.update_or_create(
                        student=student,
                        classroom=classroom,
                        attendance_date=att_date,
                        defaults={
                            'status': status,
                            'marked_by': request.user
                        }
                    )
                    saved_count += 1
                elif status == '':
                    # Remove existing record if unmarked
                    AttendanceRecord.objects.filter(
                        student=student,
                        classroom=classroom,
                        attendance_date=att_date
                    ).delete()
                    
            except Student.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Saved {saved_count} attendance records',
            'records_saved': saved_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='login')
@check_role('teacher')
def manage_class_students(request, classroom_id):
    """View for adding/removing students from a class"""
    from dashboard.models import Classroom, ClassStudent, Student
    
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('student_ids')
        
        if action == 'add':
            for sid in student_ids:
                try:
                    student = Student.objects.get(id=sid)
                    ClassStudent.objects.get_or_create(
                        classroom=classroom, student=student
                    )
                except Student.DoesNotExist:
                    continue
            messages.success(request, f'Added {len(student_ids)} student(s) to {classroom.name}')
        elif action == 'remove':
            ClassStudent.objects.filter(
                classroom=classroom, student_id__in=student_ids
            ).delete()
            messages.success(request, f'Removed {len(student_ids)} student(s) from {classroom.name}')
        
        return redirect('dashboard:manage_class_students', classroom_id=classroom.id)
    
    # GET: Show roster management page
    enrolled_ids = ClassStudent.objects.filter(classroom=classroom).values_list('student_id', flat=True)
    enrolled_students = Student.objects.filter(id__in=enrolled_ids).order_by('full_name')
    available_students = Student.objects.exclude(id__in=enrolled_ids).order_by('full_name')
    
    context = {
        'user': request.user,
        'classroom': classroom,
        'enrolled_students': enrolled_students,
        'available_students': available_students,
        'page_title': f'Manage Students - {classroom.name}',
    }
    return render(request, 'dashboards/manage_students.html', context)


@login_required(login_url='login')
@check_role('teacher')
def student_daily_notes(request, student_id):
    """View to show and manage daily notes for a specific student"""
    from dashboard.models import Student, StudentDailyNote
    from datetime import date
    
    student = get_object_or_404(Student, pk=student_id)
    notes = StudentDailyNote.objects.filter(student=student).order_by('-note_date', '-created_at')
    
    # Check if a note already exists for today
    today = date.today()
    today_note = notes.filter(note_date=today).first()
    
    context = {
        'user': request.user,
        'role_name': 'Teacher',
        'student': student,
        'notes': notes,
        'today_note': today_note,
        'today_date': today,
        'page_title': f'Daily Notes - {student.full_name}'
    }
    return render(request, 'dashboards/student_daily_notes.html', context)


@login_required(login_url='login')
@check_role('teacher')
def save_daily_note(request, student_id):
    """AJAX endpoint to save or update a daily note"""
    from django.http import JsonResponse
    from dashboard.models import Student, StudentDailyNote
    from datetime import date
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        student = get_object_or_404(Student, pk=student_id)
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        note_date_str = data.get('date') # Format: YYYY-MM-DD
        japanese_name = data.get('japanese_name')
        
        # Update japanese name if provided
        if japanese_name is not None:
            student.japanese_name = japanese_name.strip()
            student.save(update_fields=['japanese_name'])
        
        # If content is completely missing and there's no date, we might just be saving JP name
        if 'content' not in data and japanese_name is not None:
            return JsonResponse({'success': True, 'message': 'Japanese name updated successfully.'})
            
        if not content and 'content' in data:
            return JsonResponse({'success': False, 'error': 'Note content cannot be empty if saving a note'})
            
        if note_date_str:
            note_date = date.fromisoformat(note_date_str)
        else:
            note_date = date.today()
            
        # Try to find existing note for this date
        note = StudentDailyNote.objects.filter(
            student=student, 
            note_date=note_date
        ).first()
        
        if note:
            # Check 24-hour lock
            if not note.is_editable:
                return JsonResponse({
                    'success': False, 
                    'error': 'This note is older than 24 hours and can no longer be edited.'
                })
            note.content = content
            note.teacher = request.user
            note.save()
            action = 'updated'
        else:
            # Create new note
            note = StudentDailyNote.objects.create(
                student=student,
                teacher=request.user,
                note_date=note_date,
                content=content
            )
            action = 'created'
            
        return JsonResponse({
            'success': True,
            'message': f'Note {action} successfully.',
            'note': {
                'id': note.id,
                'date': note.note_date.isoformat(),
                'content': note.content,
                'teacher': note.teacher.username if note.teacher else 'Unknown',
                'created_at': note.created_at.isoformat()
            }
        })
        
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required(login_url='login')
@check_role('teacher')
def save_attendance_data(request):
    """API endpoint to save attendance data to database"""
    from django.http import JsonResponse
    from django.views.decorators.csrf import ensure_csrf_cookie
    from django.utils import timezone
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    try:
        # Parse JSON data from request
        data = json.loads(request.body)
        attendance_records = data.get('attendance', [])
        
        if not attendance_records:
            return JsonResponse({'success': False, 'error': 'No attendance data provided'})
        
        saved_count = 0
        from dashboard.models import Student
        
        for record in attendance_records:
            student_id = record.get('studentId')
            japanese_name = record.get('japaneseName', '')
            attended_dates = record.get('attendedDates', [])
            
            # Find student by ID (using database ID, not student_id field)
            try:
                student = Student.objects.get(id=student_id)
                
                # Update Japanese name
                if japanese_name is not None:
                    student.japanese_name = japanese_name
                    student.save()
                
                # Save attendance records
                from dashboard.models import AttendanceRecord
                for date_str in attended_dates:
                    # Check if attendance already exists for this date
                    attendance, created = AttendanceRecord.objects.get_or_create(
                        student=student,
                        attendance_date=date_str,
                        defaults={'status': 'present', 'marked_by': request.user}
                    )
                    if not created:
                        # Update existing record
                        attendance.status = 'present'
                        attendance.marked_by = request.user
                        attendance.save()
                    saved_count += 1
                    
            except Student.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully saved {saved_count} attendance records',
            'records_saved': saved_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required(login_url='login')
@check_role('teacher')
def student_records(request):
    """View for viewing student records with inline editable today's note and Japanese name"""
    from dashboard.models import Student, StudentDailyNote
    from datetime import date
    
    students = Student.objects.all().order_by('full_name')
    today = date.today()
    
    # Pre-fetch today's notes for efficient rendering
    today_notes = StudentDailyNote.objects.filter(note_date=today)
    notes_dict = {note.student_id: note for note in today_notes}
    
    student_data = []
    for student in students:
        student_data.append({
            'student': student,
            'today_note': notes_dict.get(student.id)
        })
        
    context = {
        'user': request.user,
        'role_name': 'Teacher',
        'student_data': student_data,
        'today_date': today,
        'page_title': 'Student Records'
    }
    return render(request, 'dashboards/student_records.html', context)

@login_required(login_url='login')
@check_role('client', 'manager', 'staff')
def recruitment_client_dashboard(request):
    # Get counts for each pipeline stage
    candidate_info_count = Student.objects.filter(stage='candidate_info').count()
    select_candidate_count = Student.objects.filter(stage='select_candidate').count()
    interview_pattern_count = Student.objects.filter(stage='interview_pattern').count()
    pass_interview_count = Student.objects.filter(stage='pass_interview').count()
    ceo_approval_count = Student.objects.filter(stage='ceo_approval').count()
    visa_arrival_count = Student.objects.filter(stage='visa_arrival').count()
    
    # Get students for each stage
    candidate_info_students = Student.objects.filter(stage='candidate_info')
    select_candidate_students = Student.objects.filter(stage='select_candidate')
    interview_pattern_students = Student.objects.filter(stage='interview_pattern')
    pass_interview_students = Student.objects.filter(stage='pass_interview')
    ceo_approval_students = Student.objects.filter(stage='ceo_approval')
    visa_arrival_students = Student.objects.filter(stage='visa_arrival')
    
    # Get active tab from URL parameter
    active_tab = request.GET.get('tab', 'candidate-info')
    
    context = {
        # Pipeline counts
        'candidate_info_count': candidate_info_count,
        'select_candidate_count': select_candidate_count,
        'interview_pattern_count': interview_pattern_count,
        'pass_interview_count': pass_interview_count,
        'ceo_approval_count': ceo_approval_count,
        'visa_arrival_count': visa_arrival_count,
        
        # Student querysets for each stage
        'candidate_info_students': candidate_info_students,
        'select_candidate_students': select_candidate_students,
        'interview_pattern_students': interview_pattern_students,
        'pass_interview_students': pass_interview_students,
        'ceo_approval_students': ceo_approval_students,
        'visa_arrival_students': visa_arrival_students,
        
        # Active tab
        'active_tab': active_tab,
        
        # User info
        'user': request.user,
        'role_name': 'Recruitment Manager',
        'role_description': 'Manage candidate recruitment pipeline',
    }
    
    return render(request, 'dashboards/recruitment_client_dashboard.html', context)



# dashboard_views.py - Complete fixed move_to_next_stage function
@login_required
def move_to_next_stage(request, student_id, next_stage):
    """Move student to next stage in pipeline"""
    
    try:
        student = get_object_or_404(Student, id=student_id)
    except Student.DoesNotExist:
        messages.error(request, f'❌ Student with ID {student_id} not found')
        return redirect('/dashboard/recruitment_client/?tab=candidate-info')
    
    # Define the pipeline sequence
    pipeline_sequence = [
        'candidate_info',
        'select_candidate', 
        'interview_pattern',
        'pass_interview',
        'ceo_approval',
        'visa_arrival',
        'completed'
    ]
    
    # Create mapping for URL-friendly names to actual stage names
    stage_mapping = {
        'candidate-info': 'candidate_info',
        'select-candidate': 'select_candidate',
        'interview-pattern': 'interview_pattern',
        'pass-interview': 'pass_interview',
        'ceo-approval': 'ceo_approval',
        'visa-arrival': 'visa_arrival',
        'completed': 'completed'
    }
    
    if next_stage in stage_mapping:
        normalized_next_stage = stage_mapping[next_stage]
    else:
        normalized_next_stage = next_stage.replace('-', '_')
    
    if student.stage not in pipeline_sequence:
        # Auto-fix invalid current stage
        student.stage = 'candidate_info'
        student.save()
        messages.warning(request, f'⚠️  Fixed invalid stage for {student.full_name}')
    
    if normalized_next_stage not in pipeline_sequence:
        valid_stages_display = [stage.replace('_', ' ').title() for stage in pipeline_sequence]
        messages.error(request, f'❌ Invalid target stage: {next_stage}. Valid stages are: {", ".join(valid_stages_display)}')
        return redirect(f'/dashboard/recruitment_client/?tab={student.stage}')
    
    try:
        current_index = pipeline_sequence.index(student.stage)
        next_index = pipeline_sequence.index(normalized_next_stage)
        
        if next_index > current_index:
            old_stage = student.stage
            student.stage = normalized_next_stage
            student.save()
            
            messages.success(request, f'✅ Successfully moved {student.full_name} to {normalized_next_stage.replace("_", " ").title()}')
        elif next_index == current_index:
            messages.warning(request, f'ℹ️  {student.full_name} is already in {normalized_next_stage.replace("_", " ").title()} stage')
        else:
            messages.error(request, f'❌ Cannot move backwards from {student.stage.replace("_", " ").title()} to {normalized_next_stage.replace("_", " ").title()}')
            
    except Exception as e:
        messages.error(request, f'❌ Unexpected error: {str(e)}')
    
    # Redirect back to the dashboard
    redirect_url = f'/dashboard/recruitment_client/?tab={student.stage}'
    print(f"🔀 Redirecting to: {redirect_url}")
    return redirect(redirect_url)