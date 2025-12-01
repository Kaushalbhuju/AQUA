from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import User
from .forms import LoginForm


@require_http_methods(["GET", "POST"])
def login_view(request):

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                # Redirect based on user role using the get_dashboard_url method
                return redirect(user.get_dashboard_url())
            else:
                messages.error(request, "Invalid username or password")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


