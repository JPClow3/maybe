import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maybe_django.settings')

app = Celery('maybe_django')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
# Set timezone first
app.conf.timezone = 'America/Sao_Paulo'

# Configure beat schedule
app.conf.beat_schedule = {
    'update-b3-prices-daily': {
        'task': 'investments.tasks.update_b3_prices',
        'schedule': crontab(hour=18, minute=0),  # 18h BRT (after B3 market close)
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
}

