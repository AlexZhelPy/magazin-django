import logging

from rest_framework import serializers
from django.contrib.auth.models import User

from ..models import Profile
from .image import ImageSerializer


logger = logging.getLogger(__name__)


class ProfileSerializer(serializers.ModelSerializer):
    """
        Схема для профиля пользователя.

        Эта схема позволяет сериализовать и десериализовать данные профиля пользователя,
        включая связанные с ним данные из модели `User` и изображение аватара.

            **Поля:**
                - `fullName`: Полное имя пользователя (связано с полем `full_name` модели `Profile`).
                - `email`: Электронная почта пользователя (связано с полем `email` модели `User`).
                - `phone`: Телефон пользователя (поле модели `Profile`).
                - `avatar`: Изображение аватара пользователя (сериализуется с помощью `ImageSerializer`).

            **Мета-класс:**
                - `model`: Модель `Profile`, на основе которой создается схема.
                - `fields`: Список полей, которые включаются в схему.
    """

    fullName = serializers.CharField(source="full_name")
    email = serializers.EmailField(source="user.email")
    phone = serializers.CharField()
    avatar = ImageSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["fullName", "email", "phone", "avatar"]

    def validate_email(self, value):
        """
            Метод для валидации электронной почты пользователя.

            Проверяет, что электронная почта не используется другим пользователем, исключая текущего пользователя.

                **Параметры:**
                    - `value`: Электронная почта для проверки.

                **Возвращаемое значение:**
                    - Валидированное значение электронной почты или исключение `ValidationError`,
                    если электронная почта уже используется.
        """

        # Получаем текущего пользователя из контекста запроса
        request = self.context.get('request')
        if request and request.user:
            current_user = request.user
            # Проверяем, существует ли электронная почта, исключая текущего пользователя
            if User.objects.filter(email=value).exclude(id=current_user.id).exists():
                raise serializers.ValidationError("Электронная почта уже используется.")
        else:
            # Если текущий пользователь не доступен, просто проверяем уникальность
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Электронная почта уже используется.")
        return value

    def validate_phone(self, value):
        """
            Метод для валидации телефона пользователя.

            Проверяет, что телефон не используется другим пользователем, исключая текущего пользователя.

                **Параметры:**
                    - `value`: Телефон для проверки.

                **Возвращаемое значение:**
                    - Валидированное значение телефона или исключение `ValidationError`,
                    если телефон уже используется.
        """

        # Получаем текущего пользователя из контекста запроса
        request = self.context.get('request')
        if request and request.user:
            current_user = request.user.profile
            # Проверяем, существует ли телефон, исключая текущего пользователя
            if Profile.objects.filter(phone=value).exclude(id=current_user.id).exists():
                raise serializers.ValidationError("Такой номер телефона уже существует.")
        else:
            # Если текущий пользователь не доступен, просто проверяем уникальность
            if Profile.objects.filter(phone=value).exists():
                raise serializers.ValidationError("Такой номер телефона уже существует.")
        return value

    def update(self, instance, validated_data):
        """
            Метод для обновления профиля пользователя.

            Обновляет поле электронной почты в модели `User` и другие поля в модели `Profile`.

                **Параметры:**
                    - `instance`: Объект профиля пользователя для обновления.
                    - `validated_data`: Валидированные данные для обновления.

                **Возвращаемое значение:**
                    - Обновленный объект профиля пользователя.
        """

        # Обновляем поле email в модели User
        if 'user' in validated_data:
            email = validated_data['user'].pop('email', None)
            if email:
                instance.user.email = email
                instance.user.save()

        # Обновляем другие поля в модели Profile
        for attr, value in validated_data.items():
            if attr != 'user':
                setattr(instance, attr, value)

        instance.save()
        return instance
