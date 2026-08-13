"""
Teacher-specific views: attendance, class management, daily notes, student records
"""
import calendar
import json
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _

from dashboard.models import Student, Classroom, ClassStudent, AttendanceRecord, StudentDailyNote, TeacherStudentRecord
from ..decorators_fixed import check_role
from .utils import localized_classroom_name


@login_required(login_url='/')
@check_role('teacher')
def student_attendance(request):
    """Redirect to class list for class-based attendance"""
    return redirect('dashboard:class_list')


@login_required(login_url='/')
@check_role('teacher')
def class_list(request):
    """View showing all classes for the teacher"""
    classrooms = Classroom.objects.all()

    if not classrooms.exists():
        for name in ['Class A', 'Class B', 'Class C', 'Class D']:
            Classroom.objects.create(name=name, teacher=request.user)
        classrooms = Classroom.objects.all()

    for classroom in classrooms:
        classroom.localized_name = localized_classroom_name(classroom.name)

    context = {
        'user': request.user,
        'role_name': 'Teacher',
        'classrooms': classrooms,
        'page_title': 'Student Attendance'
    }
    return render(request, 'dashboards/class_list.html', context)


@login_required(login_url='/')
@check_role('teacher')
def create_class(request):
    """Create a new class with a teacher-provided name"""
    if request.method != 'POST':
        return redirect('dashboard:class_list')

    name = (request.POST.get('name') or '').strip()
    if not name:
        messages.error(request, _('Class name cannot be empty.'))
        return redirect('dashboard:class_list')

    if Classroom.objects.filter(name__iexact=name).exists():
        messages.error(request, _('A class named "%(name)s" already exists.') % {'name': name})
        return redirect('dashboard:class_list')

    Classroom.objects.create(name=name, teacher=request.user)
    messages.success(request, _('Class "%(name)s" created successfully.') % {'name': name})
    return redirect('dashboard:class_list')


@login_required(login_url='/')
@check_role('teacher')
def class_attendance(request, classroom_id):
    """View for marking attendance inside a class"""
    classroom = get_object_or_404(Classroom, pk=classroom_id)
    class_students = ClassStudent.objects.filter(classroom=classroom).select_related('student')
    students = [cs.student for cs in class_students]

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

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    student_data = []
    for student in students:
        records = AttendanceRecord.objects.filter(
            student=student, classroom=classroom,
            attendance_date__year=year, attendance_date__month=month
        )
        attendance_map = {r.attendance_date.day: r.status for r in records}

        day_statuses = []
        present_count = 0
        holiday_count = 0
        for day in days:
            status = attendance_map.get(day, '')
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
        'classroom_display_name': localized_classroom_name(classroom.name),
        'student_data': student_data,
        'days': days,
        'month_name': month_name,
        'year': year,
        'month': month,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'page_title': _('Attendance - %(classroom)s') % {'classroom': localized_classroom_name(classroom.name)},
    }
    return render(request, 'dashboards/class_attendance.html', context)


@login_required(login_url='/')
@check_role('teacher')
def save_class_attendance(request, classroom_id):
    """AJAX endpoint to save O/X attendance for a class"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _('Method not allowed')})

    try:
        classroom = get_object_or_404(Classroom, pk=classroom_id)
        data = json.loads(request.body)
        records = data.get('records', [])

        if not records:
            return JsonResponse({'success': True, 'message': _('No changes to save.'), 'records_saved': 0})

        year = int(data.get('year', date.today().year))
        month = int(data.get('month', date.today().month))

        student_ids = set()
        for rec in records:
            sid = rec.get('studentId')
            if sid:
                try:
                    student_ids.add(int(sid))
                except ValueError:
                    pass

        students_dict = Student.objects.in_bulk(student_ids)

        # Track Japanese name updates
        students_to_update = []
        jp_names_updated = set()
        for rec in records:
            try:
                sid = int(rec.get('studentId'))
            except (ValueError, TypeError):
                continue
            if sid in students_dict and sid not in jp_names_updated:
                jp_name = rec.get('japaneseName', None)
                if jp_name is not None and students_dict[sid].japanese_name != jp_name:
                    students_dict[sid].japanese_name = jp_name
                    students_to_update.append(students_dict[sid])
                    jp_names_updated.add(sid)

        if students_to_update:
            Student.objects.bulk_update(students_to_update, ['japanese_name'])

        existing_records_qs = AttendanceRecord.objects.filter(
            classroom=classroom, attendance_date__year=year,
            attendance_date__month=month, student_id__in=student_ids
        )
        existing_dict = {(r.student_id, r.attendance_date.day): r for r in existing_records_qs}

        records_to_create = []
        records_to_update = []
        records_to_delete_ids = []
        saved_count = 0

        for rec in records:
            try:
                sid = int(rec.get('studentId'))
                day = int(rec.get('day'))
            except (ValueError, TypeError):
                continue
            status = rec.get('status')
            if sid not in students_dict:
                continue
            student = students_dict[sid]
            try:
                att_date = date(year, month, day)
            except ValueError:
                continue
            existing_record = existing_dict.get((sid, day))
            if status in ('present', 'absent', 'holiday'):
                if existing_record:
                    if existing_record.status != status:
                        existing_record.status = status
                        existing_record.marked_by = request.user
                        records_to_update.append(existing_record)
                        saved_count += 1
                else:
                    records_to_create.append(AttendanceRecord(
                        student=student, classroom=classroom,
                        attendance_date=att_date, status=status, marked_by=request.user
                    ))
                    saved_count += 1
            elif status == '':
                if existing_record:
                    records_to_delete_ids.append(existing_record.id)

        if records_to_create:
            AttendanceRecord.objects.bulk_create(records_to_create)
        if records_to_update:
            AttendanceRecord.objects.bulk_update(records_to_update, ['status', 'marked_by'])
        if records_to_delete_ids:
            AttendanceRecord.objects.filter(id__in=records_to_delete_ids).delete()

        return JsonResponse({
            'success': True,
            'message': _('Saved %(count)s attendance records') % {'count': saved_count},
            'records_saved': saved_count
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='/')
@check_role('teacher')
def manage_class_students(request, classroom_id):
    """View for adding/removing students from a class"""
    classroom = get_object_or_404(Classroom, pk=classroom_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('student_ids')

        if action == 'add':
            for sid in student_ids:
                try:
                    student = Student.objects.get(id=sid)
                    ClassStudent.objects.get_or_create(classroom=classroom, student=student)
                except Student.DoesNotExist:
                    continue
            messages.success(request,
                _('Added %(count)s student(s) to %(classroom)s') % {
                    'count': len(student_ids),
                    'classroom': localized_classroom_name(classroom.name),
                })
        elif action == 'remove':
            ClassStudent.objects.filter(classroom=classroom, student_id__in=student_ids).delete()
            messages.success(request,
                _('Removed %(count)s student(s) from %(classroom)s') % {
                    'count': len(student_ids),
                    'classroom': localized_classroom_name(classroom.name),
                })
        return redirect('dashboard:manage_class_students', classroom_id=classroom.id)

    enrolled_ids = ClassStudent.objects.filter(classroom=classroom).values_list('student_id', flat=True)
    enrolled_students = Student.objects.filter(id__in=enrolled_ids).order_by('full_name')
    available_students = Student.objects.exclude(id__in=enrolled_ids).order_by('full_name')

    context = {
        'user': request.user,
        'classroom': classroom,
        'classroom_display_name': localized_classroom_name(classroom.name),
        'enrolled_students': enrolled_students,
        'available_students': available_students,
        'page_title': _('Manage Students - %(classroom)s') % {'classroom': localized_classroom_name(classroom.name)},
    }
    return render(request, 'dashboards/manage_students.html', context)


@login_required(login_url='/')
@check_role('teacher')
def student_daily_notes(request, student_id):
    """View to show and manage daily notes for a specific student"""
    student = get_object_or_404(Student, pk=student_id)
    notes = StudentDailyNote.objects.filter(student=student).order_by('-note_date', '-created_at')
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


@login_required(login_url='/')
@check_role('teacher')
def save_daily_note(request, student_id):
    """AJAX endpoint to save or update a daily note"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _('Method not allowed')})

    try:
        student = get_object_or_404(Student, pk=student_id)
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        note_date_str = data.get('date')
        japanese_name = data.get('japanese_name')

        if japanese_name is not None:
            student.japanese_name = japanese_name.strip()
            student.save(update_fields=['japanese_name'])

        if 'content' not in data and japanese_name is not None:
            return JsonResponse({'success': True, 'message': _('Japanese name updated successfully.')})

        if not content and 'content' in data:
            return JsonResponse({'success': False, 'error': _('Note content cannot be empty if saving a note')})

        note_date = date.fromisoformat(note_date_str) if note_date_str else date.today()
        note = StudentDailyNote.objects.filter(student=student, note_date=note_date).first()

        if note:
            if not note.is_editable:
                return JsonResponse({
                    'success': False,
                    'error': _('This note is older than 24 hours and can no longer be edited.')
                })
            note.content = content
            note.teacher = request.user
            note.save()
            action = _('updated')
        else:
            note = StudentDailyNote.objects.create(
                student=student, teacher=request.user, note_date=note_date, content=content
            )
            action = _('created')

        return JsonResponse({
            'success': True,
            'message': _('Note %(action)s successfully.') % {'action': action},
            'note': {
                'id': note.id,
                'date': note.note_date.isoformat(),
                'content': note.content,
                'teacher': note.teacher.username if note.teacher else _('Unknown'),
                'created_at': note.created_at.isoformat()
            }
        })

    except ValueError:
        return JsonResponse({'success': False, 'error': _('Invalid date format')})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='/')
@check_role('teacher')
def save_attendance_data(request):
    """API endpoint to save attendance data to database"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': _('Method not allowed')})

    try:
        data = json.loads(request.body)
        attendance_records = data.get('attendance', [])

        if not attendance_records:
            return JsonResponse({'success': False, 'error': _('No attendance data provided')})

        saved_count = 0
        for record in attendance_records:
            student_id = record.get('studentId')
            japanese_name = record.get('japaneseName', '')
            attended_dates = record.get('attendedDates', [])

            try:
                student = Student.objects.get(id=student_id)
                if japanese_name is not None:
                    student.japanese_name = japanese_name
                    student.save()

                for date_str in attended_dates:
                    attendance, created = AttendanceRecord.objects.get_or_create(
                        student=student, attendance_date=date_str,
                        defaults={'status': 'present', 'marked_by': request.user}
                    )
                    if not created:
                        attendance.status = 'present'
                        attendance.marked_by = request.user
                        attendance.save()
                    saved_count += 1
            except Student.DoesNotExist:
                continue

        return JsonResponse({
            'success': True,
            'message': _('Successfully saved %(count)s attendance records') % {'count': saved_count},
            'records_saved': saved_count
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='/')
@check_role('teacher')
def student_records(request):
    """View for viewing student records with inline editable today's note and Japanese name"""
    enrolled_ids = TeacherStudentRecord.objects.filter(teacher=request.user).values_list('student_id', flat=True)
    students = Student.objects.filter(id__in=enrolled_ids).order_by('full_name')
    available_students = Student.objects.exclude(id__in=enrolled_ids).order_by('full_name')

    today = date.today()
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
        'enrolled_students': students,
        'available_students': available_students,
        'today_date': today,
        'page_title': 'Student Records'
    }
    return render(request, 'dashboards/student_records.html', context)


@login_required(login_url='/')
@check_role('teacher')
def manage_teacher_records(request):
    """AJAX endpoint for managing students in the Teacher Records list"""
    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('student_ids')

        if action == 'add':
            for sid in student_ids:
                try:
                    student = Student.objects.get(id=sid)
                    TeacherStudentRecord.objects.get_or_create(teacher=request.user, student=student)
                except Student.DoesNotExist:
                    continue
        elif action == 'remove':
            TeacherStudentRecord.objects.filter(teacher=request.user, student_id__in=student_ids).delete()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)