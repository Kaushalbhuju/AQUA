"""
Shared utilities for student views
"""
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def check_role(*allowed_roles):
    """Decorator to check multiple user roles"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request.user, 'role', None)
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access this page.")
            return redirect('dashboard:home')
        return wrapper
    return decorator


def save_student_form(form, request):
    """Helper to save student form and handle messages"""
    try:
        student = form.save()
        messages.success(request, f'Student {student.full_name} registered successfully with ID: {student.student_id}!')
        return student
    except Exception as e:
        messages.error(request, f'Error saving student: {str(e)}')
        return None