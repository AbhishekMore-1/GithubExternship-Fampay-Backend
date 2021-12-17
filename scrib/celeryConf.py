import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrib.settings')

# Celery App Configuration
app = Celery('scrib',broker = 'amqp://localhost')
app.autodiscover_tasks()