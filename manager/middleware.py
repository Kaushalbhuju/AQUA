"""
Middleware that automatically logs meaningful staff actions.

We keep this lightweight and low-noise:
- Only for authenticated users with role 'staff' (or optionally all roles if needed)
- Only for state-changing methods: POST, PUT, PATCH, DELETE
- Skips static/media/admin/ajax noise
- Uses the central log_staff_activity helper
"""
from .utils import log_staff_activity

# Paths to ignore entirely
IGNORE_PREFIXES = (
    '/static/',
    '/media/',
    '/admin/jsi18n/',
    '/favicon.ico',
)

# Human-friendly mapping for common staff POST paths
PATH_DESCRIPTIONS = {
    '/staff/tasks/': 'Viewed my tasks',
}

def _should_log(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return False
    # Only track staff by default; change to include other roles if desired
    # To track all staff-role users: restrict to role == 'staff'
    # If you want to track manager actions too, remove this check
    if getattr(request.user, 'role', '') != 'staff':
        return False
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return False
    path = request.path or ''
    for prefix in IGNORE_PREFIXES:
        if path.startswith(prefix):
            return False
    # Skip failed CSRF / login page POSTs handled elsewhere
    if path in ('/login/', '/accounts/login/'):
        return False
    # Skip paths that are already explicitly logged in views to avoid duplicates
    # (task status updates are logged as task_status_update)
    if '/staff/tasks/' in path and 'update' in path:
        return False
    return True

def _describe(request):
    path = request.path or ''
    method = request.method
    # Try to give a nicer description
    if 'tasks' in path and method == 'POST':
        if 'update' in path:
            return f"Updated task status via {path}"
        return f"Performed {method} on {path}"
    return f"{method} {path}"

class StaffActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log after response so we know it succeeded (2xx/3xx)
        try:
            if _should_log(request):
                # Only log successful mutating requests
                if 200 <= response.status_code < 400:
                    desc = _describe(request)
                    # Enrich with POST keys (without sensitive data)
                    extra = {}
                    try:
                        # Avoid logging passwords
                        safe_keys = [k for k in request.POST.keys() if 'password' not in k.lower()]
                        if safe_keys:
                            extra['post_keys'] = safe_keys[:10]
                            # Include status if present
                            if 'status' in request.POST:
                                extra['status'] = request.POST.get('status')
                            if 'title' in request.POST:
                                extra['title'] = request.POST.get('title')[:100]
                    except Exception:
                        pass
                    log_staff_activity(
                        user=request.user,
                        action='other',
                        description=desc,
                        request=request,
                        extra_data=extra if extra else None,
                    )
        except Exception as e:
            print(f"[StaffActivityMiddleware] logging failed: {e}")
        return response
