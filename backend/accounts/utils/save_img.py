import logging
import os

logger = logging.getLogger(__name__)

"""
    Константа, определяющая путь к директории, где будут храниться аватары пользователей.
"""
_AVATARS_PATH = os.path.join("images", "avatars")

def save_avatar(instance, filename: str) -> str:
    """
        Функция для сохранения аватара пользователя.

        Эта функция генерирует путь для сохранения аватара пользователя на основе имени пользователя и имени файла.

            **Параметры:**
                - `instance`: Объект профайла пользователя.
                - `filename`: Название файла аватара.

            **Возвращаемое значение:**
                - Строка, представляющая полный путь для сохранения аватара.
    """
    logger.debug("Сохранение аватара пользователя")

    return os.path.join(
        "media", _AVATARS_PATH, f"{instance.profile.user.username}", f"{filename}"
    )
