from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def home_view(request):
    return render(request, 'dashboards/home.html')

@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'dashboards/dashboard.html')

@login_required(login_url='login')
def profile_view(request):
    return render(request, 'dashboards/profile.html')

@login_required(login_url='login')
def settings_view(request):
    return render(request, 'dashboards/settings.html')