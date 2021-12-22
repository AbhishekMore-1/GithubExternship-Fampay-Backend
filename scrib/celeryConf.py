import os
from celery import Celery

settings_module = 'scrib.production' if 'WEBSITE_HOSTNAME' in os.environ else 'scrib.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

# Celery App Configuration
app = Celery('scrib',broker = 'amqp://localhost')
app.autodiscover_tasks()