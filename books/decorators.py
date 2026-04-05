from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def manager_or_staff_required(view_func):
    """Allow access only to manager, staff, and operation_head roles."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role in ('manager', 'staff', 'operation_head'):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('books:book_list')
    return wrapper


def manager_required(view_func):
    """Allow access only to manager and operation_head roles."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role in ('manager', 'operation_head'):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Only managers can perform this action.')
        return redirect('books:book_list')
    return wrapper
