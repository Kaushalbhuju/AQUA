from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import StaffTask

def staff_ssw_working_visa(request):
    return render(request, 'canstud/staffssw.html')

def staff_student_visa(request):
    return render(request, 'canstud/staff_stud.html')

@login_required
def my_tasks(request):
    tasks = StaffTask.objects.filter(assigned_to=request.user)
    return render(request, 'staff/my_tasks.html', {'tasks': tasks})

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(StaffTask, id=task_id, assigned_to=request.user)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(StaffTask.STATUS_CHOICES):
            task.status = status
            task.save()
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('staff:my_tasks')
