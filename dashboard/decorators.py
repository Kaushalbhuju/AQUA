from django.shortcuts import redirect

def check_role(*allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            user_role = getattr(request.user, 'role', None)

            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            from django.contrib import messages
            messages.error(request, "You do not have permission to access this page.")
            return redirect('dashboard:home')
        return wrapper
    return decorator
