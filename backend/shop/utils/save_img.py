import logging
import os

logger = logging.getLogger(__name__)

_PRODUCTS_PATH = os.path.join("images", "products")
_CATEGORIES_PATH = os.path.join("images", "categories")
_AVATARS_PATH = os.path.join("images", "avatars")


def save_img_for_product(instance, filename: str) -> str:
    """
    Сохранение изображения товара

    @param instance: объект изображения
    @param filename: название файла
    @return: строка - место хранения изображения
    """
    logger.debug("Сохранение изображения товара")

    # Создаем директорию, если она не существует
    directory = os.path.join("media", _PRODUCTS_PATH, f"{instance.product.id}")
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Сохраняем файлы в директорию с фронтендом
    try:
        return os.path.join(directory, f"{filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении изображения товара: {e}")
        raise


def save_img_for_category(instance, filename: str) -> str:
    """
    Сохранение изображения к категории

    @param instance: объект изображения
    @param filename: название файла
    @return: строка - место хранения изображения
    """
    logger.debug("Сохранение изображения категории")

    # Создаем директорию, если она не существует
    directory = os.path.join("media", _CATEGORIES_PATH, f"{instance.category.id}")
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Сохраняем файлы в директорию с фронтендом
    try:
        return os.path.join(directory, f"{filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении изображения категории: {e}")
        raise


def save_avatar(instance, filename: str) -> str:
    """
    Функция для сохранения аватара пользователя

    @param instance: объект профайла
    @param filename: название файла
    @return: path
    """
    logger.debug("Сохранение аватара пользователя")

    # Создаем директорию, если она не существует
    directory = os.path.join("static", _AVATARS_PATH, f"{instance.profile.user.username}")
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Сохраняем файлы в директорию с фронтендом
    try:
        return os.path.join(directory, f"{filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении аватара пользователя: {e}")
        raise
