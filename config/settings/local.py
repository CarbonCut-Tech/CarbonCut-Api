from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Timezone settings
USE_TZ = True
TIME_ZONE = 'UTC'

INSTALLED_APPS += [
    'corsheaders',
    'core.apps.CoreConfig',
]

# AWS/LocalStack settings
AWS_ENDPOINT_URL = 'http://localhost:4566'
AWS_ACCESS_KEY_ID = 'test'
AWS_SECRET_ACCESS_KEY = 'test'
AWS_DEFAULT_REGION = 'us-east-1'

# Set environment variables BEFORE importing Celery
os.environ['AWS_ENDPOINT_URL'] = AWS_ENDPOINT_URL
os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY
os.environ['AWS_DEFAULT_REGION'] = AWS_DEFAULT_REGION

# Celery Configuration for SQS with LocalStack
# CRITICAL: The broker URL must be in this exact format for SQS
CELERY_BROKER_URL = f'sqs://{AWS_ACCESS_KEY_ID}:{AWS_SECRET_ACCESS_KEY}@'

CELERY_BROKER_TRANSPORT_OPTIONS = {
    'region': AWS_DEFAULT_REGION,
    'polling_interval': 1,
    'visibility_timeout': 3600,
    'wait_time_seconds': 20,
    'queue_name_prefix': '',
    # This is the critical part for LocalStack
    'predefined_queues': {
        'celery': {
            'url': f'{AWS_ENDPOINT_URL}/000000000000/celery',
        }
    },
}

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_BACKEND = 'db+sqlite:///celery_results.db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

SQS_QUEUE_URL = f'{AWS_ENDPOINT_URL}/000000000000/carbon-events-queue'

# Override middleware to include CORS and remove CSRF for local dev
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('SMTP_USER')
EMAIL_HOST_PASSWORD = os.getenv('SMTP_PASS')
DEFAULT_FROM_EMAIL = os.getenv('SMTP_USER')

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

GEOS_LIBRARY_PATH = '/opt/homebrew/Cellar/gdal/3.12.1/lib/libgdal.dylib'
GDAL_LIBRARY_PATH = '/opt/homebrew/Cellar/gdal/3.12.1/lib/libgdal.dylib'