import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('django_admin_pro')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-weekly-digest': {
        'task': 'apps.accounts.tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday 9 AM
    },
    'cleanup-expired-sessions': {
        'task': 'apps.accounts.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily 2 AM
    },
    'generate-daily-report': {
        'task': 'apps.dashboard.tasks.generate_daily_report',
        'schedule': crontab(hour=1, minute=0),  # Daily 1 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
