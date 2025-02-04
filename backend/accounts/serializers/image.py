from rest_framework import serializers


class ImageSerializer(serializers.Serializer):
    """
        Схема для изображений.

        Эта схема сериализует и десериализует данные для изображений,
        включая источник изображения (`src`) и альтернативный текст (`alt`).

            **Поля:**
                - `src`: Источник изображения.
                - `alt`: Альтернативный текст для изображения.
    """

    src = serializers.CharField()
    alt = serializers.CharField(max_length=250, default="")

    class Meta:
        fields = ["src", "alt"]
