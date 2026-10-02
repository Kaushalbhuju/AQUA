from django.utils import timezone
from django.conf import settings
from ipaddress import ip_address

def get_client_ip(request):
    """Return the client IP, trusting forwarded headers only behind configured proxies."""
    if not request:
        return None
    remote_addr = request.META.get('REMOTE_ADDR', '').strip()
    trusted_proxy_count = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)
    if trusted_proxy_count:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        chain = [part.strip() for part in forwarded.split(',') if part.strip()]
        chain.append(remote_addr)
        if len(chain) > trusted_proxy_count:
            remote_addr = chain[-(trusted_proxy_count + 1)]
    try:
        return str(ip_address(remote_addr)) if remote_addr else None
    except ValueError:
        return None

def log_staff_activity(user, action, description='', request=None, extra_data=None):
    """
    Central helper to create a StaffActivityLog entry.
    Safe to call even if user is None / anonymous – will still create a log with snapshots.
    """
    from .models import StaffActivityLog
    import traceback
    try:
        ip = get_client_ip(request) if request else None
        ua = ''
        path = ''
        method = ''
        if request:
            try:
                ua = (request.META.get('HTTP_USER_AGENT') or '')[:1000]
            except Exception:
                ua = ''
            try:
                path = (getattr(request, 'path', '') or '')[:500]
            except Exception:
                path = ''
            try:
                method = (getattr(request, 'method', '') or '')[:10]
            except Exception:
                method = ''

        username_snapshot = ''
        role_snapshot = ''
        if user and getattr(user, 'is_authenticated', False):
            username_snapshot = getattr(user, 'username', '') or ''
            role_snapshot = getattr(user, 'role', '') or ''
        elif user and getattr(user, 'username', None):
            username_snapshot = user.username
            role_snapshot = getattr(user, 'role', '') or ''

        # Validate action
        valid_actions = {c[0] for c in StaffActivityLog.ACTION_CHOICES}
        if action not in valid_actions:
            action = 'other'

        StaffActivityLog.objects.create(
            user=user if (user and getattr(user, 'pk', None)) else None,
            username_snapshot=username_snapshot,
            role_snapshot=role_snapshot,
            action=action,
            description=description or '',
            ip_address=ip if ip else None,
            user_agent=ua,
            path=path,
            method=method,
            extra_data=extra_data,
        )
    except Exception as e:
        # Never break the main request because of logging failure; use print for debug
        print(f"[ActivityLog] Failed to log {action}: {e}")
        traceback.print_exc()
