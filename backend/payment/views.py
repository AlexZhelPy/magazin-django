import logging
import time
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from catalog.models import Product
from order.models import Order
from order.serializers import PaymentSerializer
from core.tasks import process_payment
from core.swagger import order_id

logger = logging.getLogger(__name__)


class PaymentView(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Product.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["payment"],
        manual_parameters=[order_id],
        request_body=PaymentSerializer(),
        responses={200: "successful operation"},
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Оплата заказа
        """
        serializer = PaymentSerializer(data=request.data)

        if serializer.is_valid():
            order_id = kwargs["pk"]
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response(
                    {"message": "Заказ не найден"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Запуск задачи Celery для обработки оплаты
            process_payment(order_id=order_id, data=serializer.validated_data)

            return Response({"message": "Оплата обрабатывается"}, status=status.HTTP_202_ACCEPTED)
        else:
            # Имитация ожидания оплаты заказа
            time.sleep(5)
            order_id = kwargs["pk"]
            try:
                order = Order.objects.get(id=order_id)
                order.status = 7
                order.save()
            except Order.DoesNotExist:
                pass

            logging.error(f"Невалидные данные: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
