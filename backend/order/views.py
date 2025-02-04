import logging

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import JsonResponse, Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework import status, mixins, generics
from rest_framework.response import Response

from .models import Order
from .serializers import OrderIdSerializer, OrderSerializer
from .services import OrderService
from basket.services import BasketService
from basket.serializers import BasketSerializer


logger = logging.getLogger(__name__)


class OrderView(APIView):
    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]  # Разрешено только авторизованным пользователям

    @swagger_auto_schema(
        tags=["order"],
        request_body=BasketSerializer(many=True),
        responses={200: OrderIdSerializer()},
    )
    def post(self, request):
        """
        Создание заказа (первичное)
        """

        serializer = BasketSerializer(data=request.data, many=True)

        if serializer.is_valid(raise_exception=True):

            order_id = OrderService.create(
                data=serializer.validated_data, user=request.user
            )
            # Очистка кэша с заказами пользователя
            cache.delete(f"orders_{request.user}")
            return JsonResponse({"orderId": order_id})

        else:
            logging.error(f"Невалидные данные: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["order"], responses={200: OrderSerializer(many=True)})
    def get(self, request):
        """
        Вывод списка заказов
        """
        user = request.user

        queryset = cache.get_or_set(
            f"orders_{user.id}",
            Order.objects.filter(user=user),
        )
        serializer = OrderSerializer(queryset, many=True)

        return JsonResponse(serializer.data, safe=False)


class OrderDetailView(
    mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView
):
    """
    Вывод данных и редактирование заказа
    """
    serializer_class = OrderSerializer

    def get_queryset(self):
        try:
            data = Order.objects.get(id=self.kwargs["pk"])
            return data

        except (ObjectDoesNotExist, KeyError):
            raise Http404

    @swagger_auto_schema(tags=["order"], responses={200: OrderSerializer()})
    def get(self, request, *args, **kwargs):
        """
        Вывод данных о заказе
        """
        serializer = OrderSerializer(self.get_queryset())

        return JsonResponse(serializer.data, safe=False)

    @swagger_auto_schema(
        tags=["order"],
        request_body=OrderSerializer(),
        responses={
            200: "successful operation",
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Подтверждение заказа (добавление данных о покупателе, адресе и типе доставки и т.п.)
        """
        logger.debug("Подтверждение заказа")

        data = request.data
        OrderService.update(data)
        logger.info("Заказ подтвержден")

        # Очистка кэша с заказами пользователя
        cache.delete(f"orders_{request.user}")

        BasketService.clear(request.user)

        return JsonResponse({"orderId": data["orderId"]})
