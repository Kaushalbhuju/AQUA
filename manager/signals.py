from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

from .utils import log_staff_activity

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    log_staff_activity(
        user=user,
        action='login',
        description=f"User {user.username} logged in",
        request=request,
        extra_data={'role': getattr(user, 'role', '')}
    )

@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    # user may be None if logout called without authenticated user
    who = getattr(user, 'username', 'Unknown') if user else 'Unknown'
    log_staff_activity(
        user=user,
        action='logout',
        description=f"User {who} logged out",
        request=request,
        extra_data={'role': getattr(user, 'role', '') if user else ''}
    )


# Note: StaffTask assignment is logged explicitly in manager/views.manage_tasks
# and staff/views.update_task_status to include request context (IP, path).
# No automatic post_save signal here to avoid duplicate entries.
