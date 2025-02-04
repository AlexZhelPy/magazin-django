import logging

from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from .serializers import BasketSerializer
from .swagger import basket_data
from .services import BasketService, BasketSessionService


logger = logging.getLogger(__name__)


class BasketView(APIView):
    """
    Класс для работы с корзиной товаров.
    """
    @swagger_auto_schema(tags=["basket"], responses={200: BasketSerializer(many=True)})
    def get(self, request):
        """
        Получить товары в корзине пользователя.
        Если пользователь аутентифицирован, то товары извлекаются из базы данных.
        В противном случае, товары извлекаются из сессии.
        """
        try:
            if request.user.is_authenticated:
                queryset = BasketService.get_basket(
                    request
                )  # Товары аутентифицированного пользователя из БД
            else:
                queryset = BasketSessionService.get_basket(
                    request
                )  # Товары гостя из сессии

            serializer = BasketSerializer(queryset, many=True)
            return JsonResponse(serializer.data, safe=False)
        except Exception as e:
            logger.error(f"Ошибка при получении товаров из корзины: {e}")
            return JsonResponse({"error": "Ошибка при получении товаров из корзины"}, status=500)

    @swagger_auto_schema(
        tags=["basket"],
        manual_parameters=[basket_data],
        responses={200: BasketSerializer(many=True)},
    )
    def post(self, request):
        """
        Добавить товар в корзину.
        Если пользователь аутентифицирован, то товар добавляется в корзину аутентифицированного пользователя.
        В противном случае, товар добавляется в сессию.
        """
        try:
            if request.user.is_authenticated:
                queryset = BasketService.add(
                    request
                )  # Добавить товар в корзину аутентифицированного пользователя (в БД)
            else:
                queryset = BasketSessionService.add(request)  # Записать данные в сессию
            serializer = BasketSerializer(queryset, many=True)

            return JsonResponse(serializer.data, safe=False)
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара в корзину: {e}")
            return JsonResponse({"error": "Ошибка при добавлении товара в корзину"}, status=500)

    @swagger_auto_schema(
        tags=["basket"],
        manual_parameters=[basket_data],
        responses={200: BasketSerializer(many=True)},
    )
    def delete(self, request):
        """
        Удалить товар из корзины.
        Если пользователь аутентифицирован, то товар удаляется из базы данных.
        В противном случае, товар удаляется из сессии.
        """
        try:
            if request.user.is_authenticated:
                queryset = BasketService.delete(request)  # Удалить товар из БД
            else:
                queryset = BasketSessionService.delete(request)  # Удалить из сессии

            serializer = BasketSerializer(queryset, many=True)

            return JsonResponse(serializer.data, safe=False)
        except Exception as e:
            logger.error(f"Ошибка при удалении товара из корзины: {e}")
            return JsonResponse({"error": "Ошибка при удалении товара из корзины"}, status=500)
