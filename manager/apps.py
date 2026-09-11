from django.apps import AppConfig


class ManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manager'

    def ready(self):
        # Import signals so login/logout are tracked
        try:
            import manager.signals  # noqa: F401
        except Exception as e:
            print(f"[ManagerConfig] signals import failed: {e}")
