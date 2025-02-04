from django.contrib.auth.models import User

from .utils.save_img import save_avatar
from .config import STATUS_CHOICES
from django.db import models


class Profile(models.Model):
    """
        Модель для хранения дополнительных данных о пользователе (профайл).

        Эта модель связана с моделью `User` через поле `OneToOneField`
        и позволяет хранить дополнительную информацию о пользователе.
    """

    """
        Поле, связывающее профиль с пользователем. При удалении пользователя будет удален и его профиль.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="пользователь"
    )

    """
        Поле для хранения полного имени пользователя.
    """
    full_name = models.CharField(max_length=150, verbose_name="ФИО", null=True, blank=True)

    """
        Поле для хранения телефона пользователя. Телефон должен быть уникальным.
    """
    phone = models.CharField(
        unique=False, max_length=10, null=True, verbose_name="телефон"
    )

    """
        Поле для мягкого удаления профиля. Позволяет помечать профиль как удаленный без фактического удаления из базы данных.
    """
    deleted = models.BooleanField(
        choices=STATUS_CHOICES, default=False, verbose_name="Статус"
    )  # Мягкое удаление

    class Meta:
        """
            Метакласс для настройки таблицы в базе данных.
        """
        db_table = "profile"
        verbose_name = "профиль"
        verbose_name_plural = "учетные записи"

    def __str__(self):
        """
            Метод для строкового представления объекта профиля. Возвращает полное имя пользователя.
        """
        return self.full_name


class ImageForAvatar(models.Model):
    """
        Модель для хранения данных об аватарах пользователей.

        Эта модель связана с моделью `Profile` через поле `OneToOneField` и позволяет хранить изображения аватаров.
    """

    """
        Поле для хранения пути к изображению аватара. 
        Изображение будет сохранено в директории, указанной в функции `save_avatar`.
    """
    path = models.ImageField(upload_to=save_avatar, verbose_name="изображение")

    """
        Поле для хранения альтернативного текста для изображения аватара.
    """
    alt = models.CharField(max_length=250, verbose_name="alt")

    """
        Поле, связывающее аватар с профилем пользователя. При удалении профиля будет удален и его аватар.
    """
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, verbose_name="профиль", related_name="avatar"
    )

    class Meta:
        """
            Метакласс для настройки таблицы в базе данных.
        """
        db_table = "images_for_avatars"
        verbose_name = "аватар"
        verbose_name_plural = "аватары"

    @property
    def src(self) -> str:
        """
            Переопределяем path для подстановки в frontend и корректного отображения картинки
        """
        return f"/media/{self.path}"

    def __str__(self) -> str:
        """
            Метод для строкового представления объекта аватара. Возвращает строковое представление пути к изображению.
        """
        return str(self.path)
