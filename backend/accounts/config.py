from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Статусы для мягкого удаления записей
STATUS_CHOICES = [
    (True, "Удалено"),
    (False, "Активно"),
]
