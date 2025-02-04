import json
import logging

from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers.login_and_register import UserRegisterSerializer
from .serializers.login_and_register import UserLoginSerializer
from basket.services import BasketService


logger = logging.getLogger(__name__)


@swagger_auto_schema(
    tags=["auth"],
    method="post",
    request_body=UserRegisterSerializer,
    responses={201: "The user is registered", 400: "Invalid data"},
)
@api_view(["POST"])
@permission_classes([AllowAny])  # Разрешено любому пользователю
def register_user(request):
    """
        Регистрация пользователя.

        Этот метод позволяет зарегистрировать нового пользователя через API.

            **Параметры:**
                - `request`: Объект запроса Django.

            **Входные данные:**
                - `request.body`: JSON-данные для регистрации пользователя, включающие `username`, `password` и другие необходимые поля.

            **Возвращаемое значение:**
                - `Response`: HTTP 201, если пользователь зарегистрирован успешно, или HTTP 400, если данные невалидны.
    """
    logging.debug("Регистрация пользователя")

    data = json.loads(request.body)
    serializer = UserRegisterSerializer(data=data)

    if serializer.is_valid():

        user = (
            serializer.save()
        )  # Создаем и возвращаем нового пользователя в методе create() в схеме
        # Аутентификация
        user = authenticate(
            username=user.username, password=serializer.validated_data["password"]
        )
        login(request, user)  # Авторизация нового пользователя

        BasketService.merger(request=request, user=user)  # Слияние корзин

        return Response(status=status.HTTP_201_CREATED)

    logging.error(f"Невалидные данные: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    tags=["auth"],
    method="post",
    request_body=UserLoginSerializer,
    responses={200: "The user is authenticated", 400: "Invalid data"},
)
@api_view(["POST"])
@permission_classes([AllowAny])  # Разрешено любому пользователю
def user_login(request):
    """
        Авторизация пользователя.

        Этот метод позволяет авторизовать пользователя через API.

            **Параметры:**
                - `request`: Объект запроса Django.

            **Входные данные:**
                - `request.body`: JSON-данные для авторизации пользователя, включающие `username` и `password`.

            **Возвращаемое значение:**
                - `Response`: HTTP 200, если пользователь авторизован успешно, или HTTP 400, если данные невалидны.
    """
    logging.debug("Авторизация пользователя")

    data = json.loads(request.body)
    serializer = UserLoginSerializer(data=data)

    if serializer.is_valid(raise_exception=True):
        user = authenticate(
            username=data["username"], password=data["password"]
        )  # Аутентификация
        login(request, user)  # Авторизация нового пользователя
        logging.info(f"Пользователь аутентифицирован")

        BasketService.merger(request=request, user=user)  # Слияние корзин

        return Response(None, status=status.HTTP_200_OK)

    else:
        logging.error(f"Невалидные данные: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    tags=["auth"],
    method="post",
    responses={
        200: "The user logged out of the account",
        403: "The user is not logged in",
    },
)
@api_view(["POST"])
@permission_classes(
    [IsAuthenticated]
)  # Разрешено только аутентифицированным пользователям
def user_logout(request):
    """
        Выход из учетной записи пользователя.

        Этот метод позволяет выйти из учетной записи пользователя через API.

            **Параметры:**
                - `request`: Объект запроса Django.

            **Возвращаемое значение:**
                - `Response`: HTTP 200, если пользователь вышел из учетной записи успешно.
    """
    logging.debug("Выход из учетной записи")
    logout(request)

    return Response(None, status=status.HTTP_200_OK)
