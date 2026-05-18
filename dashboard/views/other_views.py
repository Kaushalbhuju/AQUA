from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def home_view(request):
    # Redirect based on user role
    if request.user.role == 'manager':
        return redirect('dashboard:manager_dashboard')
    elif request.user.role == 'staff':
        return redirect('dashboard:staff_dashboard')
    elif request.user.role == 'operation_head':
        return redirect('dashboard:operation_head')
    elif request.user.role == 'student':
        return redirect('candidate_portal:candidate_dashboard')
    else:
        return redirect('accounts:login_view')

@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'dashboards/dashboard.html')

@login_required(login_url='login')
def profile_view(request):
    return render(request, 'dashboards/profile.html')

@login_required(login_url='login')
def settings_view(request):
    return render(request, 'dashboards/settings.html')