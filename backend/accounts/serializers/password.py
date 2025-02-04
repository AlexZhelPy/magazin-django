from rest_framework import serializers


class PasswordSerializer(serializers.Serializer):
    """
        Схема для обновления пароля пользователя.

        Эта схема позволяет сериализовать и десериализовать данные для обновления пароля пользователя.

            **Поля:**
                - `password`: Новый пароль пользователя.
                - `passwordReply`: Повторный ввод нового пароля для подтверждения.

            **Мета-класс:**
                - `fields`: Список полей, которые включаются в схему.
    """

    password = serializers.CharField()
    passwordReply = serializers.CharField()


    class Meta:
        fields = ["password", "passwordReply"]

    def validate(self, data):
        """
            Метод для валидации данных.

            Проверяет, что пароль и его подтверждение совпадают.
        """
        if data['password'] != data['passwordReply']:
            raise serializers.ValidationError("Пароли не совпадают.")
        return data

    def update(self, instance, validated_data):
        """
            Метод для обновления пароля пользователя.

            Обновляет пароль пользователя и хеширует его с помощью встроенного метода `set_password` из Django.

                **Параметры:**
                    - `instance`: Объект профиля пользователя для обновления.
                    - `validated_data`: Валидированные данные для обновления.

                **Возвращаемое значение:**
                    - Обновленный объект профиля пользователя.
        """

        instance.user.set_password(validated_data['password'])
        instance.user.save()
        return instance
