from django.contrib.auth import get_user_model
from rest_framework import serializers

from ..models import Profile


User = get_user_model()


class UserLoginSerializer(serializers.Serializer):
    """
        Схема для ввода данных для авторизации пользователя.

        Эта схема сериализует и десериализует данные для авторизации пользователя, включая имя пользователя и пароль.
    """

    username = serializers.CharField(max_length=300, required=True, label="username")
    password = serializers.CharField(
        required=True,
        write_only=True,
        label="password",
        style={"input_type": "password"},
        trim_whitespace=False,
    )


class UserRegisterSerializer(UserLoginSerializer):
    """
        Схема для ввода данных при регистрации пользователя.

        Эта схема расширяет `UserLoginSerializer` и добавляет поле для имени пользователя.
    """
    name = serializers.CharField(max_length=300, required=True, label="name")

    def create(self, validated_data):
        """
            Метод для регистрации нового пользователя.

            Создает нового пользователя с указанным именем пользователя, паролем и создает связанный профиль.

                **Параметры:**
                    - `validated_data`: Валидированные данные для регистрации.

                **Возвращаемое значение:**
                    - Объект нового пользователя.
        """

        user = User(username=validated_data["username"])
        user.set_password(validated_data["password"])
        user.save()
        Profile.objects.create(full_name=validated_data["name"], user=user)

        return user
