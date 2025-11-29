from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.UUIDField'
    name = 'finance'

    def ready(self):
        import finance.signals  # noqa

