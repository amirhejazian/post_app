import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "posts_app.settings")

app = Celery(
    "posts_app",
    broker=settings.CELERY_BROKER_URL,
    broker_connection_retry_on_startup=True,
)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
