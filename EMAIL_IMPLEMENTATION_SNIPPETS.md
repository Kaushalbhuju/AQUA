# Email Notification System - Code Snippets

## 1. Email Configuration (rm_system/settings.py)
```python
# Gmail SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'kaushalbhuju467@gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  # App Password
DEFAULT_FROM_EMAIL = 'SSW Academy Nepal <kaushalbhuju467@gmail.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
```

## 2. Email Service (appointment/emails.py)
```python
class AppointmentEmailService:
    @staticmethod
    def send_booking_confirmation(appointment, request=None):
        subject
