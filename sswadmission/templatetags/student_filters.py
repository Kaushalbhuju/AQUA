# sswadmission/templatetags/student_filters.py
from django import template

register = template.Library()

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def format_currency(value):
    """Format as currency"""
    try:
        return f"₹{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"₹0.00"