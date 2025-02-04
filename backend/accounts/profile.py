import logging

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import os

from .models import Profile
from .models import ImageForAvatar
from .serializers.password import PasswordSerializer
from .serializers.profile import ProfileSerializer
from .serializers.image import ImageSerializer


logger = logging.getLogger(__name__)


class ProfileView(APIView):
    """
        Класс для управления данными профайла пользователя.

        Этот класс предоставляет методы для получения и обновления данных профайла.
    """

    @swagger_auto_schema(
        tags=["profile"], responses={200: ProfileSerializer, 404: "No data found"}
    )
    def get(self, request, format=None):
        """
            Возвращает данные профайла пользователя.

                **Параметры:**
                    - `request`: Объект запроса Django.
                    - `format`: Формат ответа (необязательный).

                **Возвращаемое значение:**
                    - `JsonResponse`: JSON-ответ с данными профайла или HTTP 404, если профайл не найден.
        """
        logging.debug("Вывод данных профайла")

        try:
            profile = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(profile)  # Сериализация данных

            return JsonResponse(serializer.data)  # Преобразуем и отправляем JSON

        except ObjectDoesNotExist:
            logger.error("Нет данных профайла")
            return Response(status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=["profile"],
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer, 404: "No data found"},
    )
    def post(self, request, format=None):
        """
            Обновляет данные профайла пользователя.

                **Параметры:**
                    - `request`: Объект запроса Django.
                    - `format`: Формат ответа (необязательный).

                **Входные данные:**
                    - `request.data`: JSON-данные для обновления профайла.

                **Возвращаемое значение:**
                    - `JsonResponse`: JSON-ответ с обновленными данными профайла или HTTP 400, если данные невалидны.
        """
        logging.debug("Обновление данных профайла")
        serializer = ProfileSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            logger.debug(f"Данные валидны: {serializer.validated_data}")
            profile = Profile.objects.get(user=request.user)

            profile = serializer.update(profile, serializer.validated_data)
            serializer = ProfileSerializer(profile)  # Сериализация данных
            print('data =', serializer.data)


            logger.info("Данные профайла обновлены")
            return JsonResponse(serializer.data)  # Преобразуем и отправляем JSON

        else:
            logging.error(f"Невалидные данные: {serializer.errors}")
            print('serializer.errors ==', serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    tags=["profile"],
    methods=["post"],
    responses={200: ImageSerializer, 400: "Error updating avatar"},
)
@api_view(["POST"])
@permission_classes(
    [IsAuthenticated]
)  # Разрешено только аутентифицированным пользователям
def update_avatar(request):
    """
        Обновляет аватар пользователя.

            **Параметры:**
                - `request`: Объект запроса Django.

            **Входные данные:**
                - `request.FILES["avatar"]`: Изображение для обновления аватара.

            **Возвращаемое значение:**
                - `JsonResponse`: JSON-ответ с данными обновленного аватара или HTTP 400, если обновление не удалось.
    """
    logging.debug("Обновление аватара")

    avatar = request.FILES["avatar"]
    profile = Profile.objects.get(user=request.user)

    # Уменьшаем изображение до фиксированного размера
    max_width, max_height = 200, 200
    img = Image.open(avatar)
    img.thumbnail((max_width, max_height))
    thumb_io = BytesIO()
    img.save(thumb_io, format='JPEG', quality=90)
    thumb_io.seek(0)

    # Создаем или обновляем аватар
    image, created = ImageForAvatar.objects.get_or_create(profile=profile)
    image.path.save(avatar.name,
                    InMemoryUploadedFile(thumb_io, 'ImageField', avatar.name, 'image/jpeg', thumb_io.tell, None))
    image.alt = "Аватар"
    image.save()

    profile.avatar = image
    profile.save()
    logger.info("Аватарка обновлена")

    serializer = ImageSerializer(image)

    response_data = serializer.data
    response_data['redirect'] = reverse('profile').replace("/api", "", 1)

    return JsonResponse(response_data)  # Преобразуем и отправляем JSON


@swagger_auto_schema(
    tags=["profile"],
    methods=["post"],
    request_body=PasswordSerializer,
    responses={200: "password updated", 400: "Invalid data"},
)
@api_view(["POST"])
@permission_classes(
    [IsAuthenticated]
)  # Разрешено только аутентифицированным пользователям
def update_password(request):
    """
        Обновляет пароль пользователя.

            **Параметры:**
                - `request`: Объект запроса Django.

            **Входные данные:**
                - `request.data`: JSON-данные для обновления пароля.

            **Возвращаемое значение:**
                - `Response`: HTTP 200, если пароль обновлен успешно, или HTTP 400, если данные невалидны.
    """
    logging.debug("Обновление пароля")

    serializer = PasswordSerializer(data=request.data)

    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data["password"])  # Обновляем пароль
        user.save()
        logger.info("пароль обновлен")

        # Аутентификация и авторизация пользователя
        user = authenticate(
            username=user.username, password=serializer.validated_data["password"]
        )
        login(request, user)

        return Response(status=status.HTTP_200_OK)

    else:
        logging.error(f"Невалидные данные: {serializer.errors}")
        return Response(status=status.HTTP_400_BAD_REQUEST)
