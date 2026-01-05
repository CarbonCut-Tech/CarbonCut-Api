from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

app = Celery('carboncut')

app.config_from_object('django.conf:settings', namespace='CELERY')

import boto3
from botocore.config import Config as BotoConfig

_original_client = boto3.client

def _patched_client(service_name, **kwargs):
    if service_name == 'sqs':
        kwargs.setdefault('endpoint_url', 'http://localhost:4566')
        kwargs.setdefault('aws_access_key_id', 'test')
        kwargs.setdefault('aws_secret_access_key', 'test')
        kwargs.setdefault('region_name', 'us-east-1')
        kwargs['use_ssl'] = False
        kwargs['verify'] = False
    return _original_client(service_name, **kwargs)

boto3.client = _patched_client

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process-active-sessions': {
        'task': 'core.tasks.process_active_sessions_task',
        'schedule': crontab(minute='*/5'),
    },
    'mark-inactive-sessions': {
        'task': 'core.tasks.mark_inactive_sessions_task',
        'schedule': crontab(minute='*/10'),
    },
    'retry-failed-events': {
        'task': 'core.tasks.retry_failed_events',
        'schedule': crontab(minute='*/5'),
    },
    'process-dlq-messages': {
        'task': 'core.tasks.process_dlq_messages',
        'schedule': crontab(minute='*/10'),
    },
    # 'poll-google-ads': {
    #     'task': 'domain.internet.ads.tasks.poll_google_ads_task',
    #     'schedule': crontab(hour='*/24'),
    # },
}