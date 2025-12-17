# # Create sswadmission/templatetags/custom_filters.py
# from django import template

# register = template.Library()

# @register.filter
# def percentage(value, total):
#     try:
#         return (float(value) / float(total)) * 100
#     except (ValueError, ZeroDivisionError):
#         return 0


# custom_filters.py (or create it if it doesn't exist)
from django import template

register = template.Library()

@register.filter
def has_perm(user, perm):
    """Check if user has specific permission"""
    return user.has_perm(perm)