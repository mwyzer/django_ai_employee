# dj_ai_employee_main/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj_ai_employee_main.settings")

app = Celery("dj_ai_employee_main")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
