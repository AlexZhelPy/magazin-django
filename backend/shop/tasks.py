import logging
import time
from typing import Dict
from celery import shared_task
from django.db import transaction
from .models import Order, Product

logger = logging.getLogger(__name__)

@shared_task()
def process_payment(order_id: int, data: Dict) -> bool:
    """
    Обработка оплаты заказа
    """
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            number = data["number"]

            logger.info(
                f"Оплата заказа: №{order_id}, карта №{number}, сумма к оплате - {order.total_cost}"
            )

            order.status = 4  # Смена статуса заказа на "Подтверждение оплаты"
            order.save()

            # Имитация ожидания оплаты заказа
            time.sleep(5)

            # Обновляем количество товара
            order_items = order.products.all()
            for item in order_items:
                product = item.product
                product.count -= item.count
                product.sold_goods += item.count
                product.save()

            order.status = 5  # Смена статуса заказа на "Оплачен"
            order.save()
            logger.info(f"Заказ #{order_id} успешно оплачен")
            return True


    except Order.DoesNotExist:
        logger.error(f"Заказ №{order_id} не найден!")
        return False
    except Exception as e:
        logger.error(f"Ошибка при обработке оплаты заказа №{order_id}: {str(e)}")
        return False