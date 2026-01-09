# crm/settings.py - Django-crontab and Celery configuration

# Django-crontab configuration
INSTALLED_APPS = [
    'django_crontab',
    'django_celery_beat',
]

CRONJOBS = [
    # Heartbeat logger - runs every 5 minutes
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    
    # Low stock updater - runs every 12 hours (at minute 0 of every 12th hour)
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
