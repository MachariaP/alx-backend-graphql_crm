# crm/settings.py - Django-crontab configuration
INSTALLED_APPS = [
    'django_crontab',
]

CRONJOBS = [
    # Heartbeat logger - runs every 5 minutes
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    
    # Low stock updater - runs every 12 hours (at minute 0 of every 12th hour)
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]
