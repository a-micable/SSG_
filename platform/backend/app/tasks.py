from celery import Celery
import os
from .services.analyzer_service import AnalyzerService

CELERY_BROKER = os.environ.get('CELERY_BROKER', 'redis://redis:6379/0')
celery_app = Celery('platform_tasks', broker=CELERY_BROKER)


@celery_app.task
def analyze_task(path: str):
    service = AnalyzerService(root=path)
    return service.run()
