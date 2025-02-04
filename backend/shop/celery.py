import os
from celery import Celery
import redis

# Проверяем, что settings.py Django-приложения доступен через ключ DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Инициализируем Celery, указав местоположение основной директории Celery - текущую (где celery.py)
app = Celery("backend")
# Проверяем, что директория проекта существует и доступна
if not os.path.exists(os.path.dirname(__file__)):
    raise ValueError("Директория проекта не найдена")

# Определяем файл настроек Django в качестве файла конфигурации для Celery,
# предоставив пространство имен "CELERY"
app.config_from_object("django.conf:settings", namespace="CELERY")
try:
    # Проверка соединения с Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_client.ping()
except redis.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
    # Дополнительные действия при ошибке соединения
else:
    # Если соединение успешно, продолжаем работу
    app.autodiscover_tasks()
# Автоматическая загрузка фоновых задач из всех зарегистрированных приложений
# Автоматический поиск в файлах tasks.py в директориях приложений, н-р, app_shop/tasks.py
# app.autodiscover_tasks()

# Дополнительная проверка, что файл settings.py доступен
try:
    from django.conf import settings
    if not settings:
        raise ValueError("Файл settings.py не найден или не доступен")
except ImportError as e:
    raise ValueError("Ошибка импорта файла settings.py: " + str(e))
