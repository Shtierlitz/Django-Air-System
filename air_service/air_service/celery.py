from __future__ import absolute_import, unicode_literals
import os
from django.apps import apps

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'air_service.settings')

app = Celery("air_service")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])


