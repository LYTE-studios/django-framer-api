import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

app = Celery('api')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'generate-blog-posts': {
        'task': 'blogs.tasks.generate_blog_posts',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
    'retry-failed-posts': {
        'task': 'blogs.tasks.retry_failed_posts',
        'schedule': crontab(hour='*/2'),  # Run every 2 hours
    },
}