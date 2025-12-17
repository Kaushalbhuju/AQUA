# sswadmission/templatetags/permission_tags.py
from django import template

register = template.Library()

@register.simple_tag
def has_perm(user, perm):
    return user.has_perm(perm)