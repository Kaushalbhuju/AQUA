"""
Shared utilities for dashboard views
"""
from django.utils.translation import gettext as _


def localized_classroom_name(name):
    mapping = {
        'Class A': _('Class A'),
        'Class B': _('Class B'),
        'Class C': _('Class C'),
        'Class D': _('Class D'),
    }
    return mapping.get(name, name)