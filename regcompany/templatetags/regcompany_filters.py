from django import template

register = template.Library()

@register.filter
def sum_attr(queryset, attr):
    """
    Sum the values of a specific attribute in a queryset
    """
    return sum(getattr(item, attr, 0) for item in queryset)

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary using a variable as key
    """
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """
    Multiply value by argument
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0