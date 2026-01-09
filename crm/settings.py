# crm/settings.py (if you need to create it)
INSTALLED_APPS = [
    'django_crontab',
]

CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
]
