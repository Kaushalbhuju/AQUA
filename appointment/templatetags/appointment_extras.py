from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg=' '):
    """Split a string by given argument"""
    if value:
        return value.split(arg)
    return []

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key, 0)

@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0