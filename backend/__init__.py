import backend.catalog
from backend.utils.status import STATUS_CHOICES
from backend.basket.services import BasketService
from backend.core.celery import app as celery_app
__all__ = ('celery_app',)