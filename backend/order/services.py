import logging
from typing import List,Dict

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import Http404

from rest_framework import status

from basket.models import Basket
from basket.services import BasketService
from order.models import Order, PurchasedProduct, DeliveryCondition

logger = logging.getLogger(__name__)


class OrderService:
    """
    Сервис для оформления и вывода данных о заказах
    """

    @classmethod
    def get(cls, order_id: int):
        """
        Поиск и возврат заказа по id
        """
        try:
            return Order.objects.get(id=order_id)

        except ObjectDoesNotExist:
            logger.error("Заказ не найден")
            raise Http404

    @classmethod
    def create(cls, data: List[Basket], user: User) -> int:
        """
        Создание заказа
        """
        logger.debug("Создание заказа")

        order = Order.objects.create(user=user)
        new_records = []

        for product in data:
            product = dict(product)
            if product["count"] > product["product_count"]:
                product["count"] = product["product_count"]
            record = PurchasedProduct(
                order=order,
                product_id=product["product"]["id"],
                count=product["count"],
                current_price=product["current_price"],
            )
            new_records.append(record)
        PurchasedProduct.objects.bulk_create(new_records)
        BasketService.clear(user)  # Очистка корзины

        return order.id

    @classmethod
    def update(cls, data: Dict) -> None:
        """
        Подтверждение заказа (обновление введенных данных)
        """
        order = cls.get(order_id=data["orderId"])

        all_users = User.objects.all()
        all_emails = {user.email: user for user in all_users}

        # Проверить на совпадение email
        if data["email"] in all_emails:
            # Сравнить пользователей
            user_from_db = all_emails[data["email"]]
            if order.user != user_from_db:
                error_message = f"Пользователь из заказа не совпадает с пользователем, которому принадлежит email {data['email']}"
                raise ValidationError(error_message, code=status.HTTP_400_BAD_REQUEST)
        else:
            # Записать введенный email текущему пользователю
            order.user.email = data["email"]
            order.user.save()

        # Проверка на пустые поля
        required_fields = ["fullName", "email", "phone", "city", "address"]
        for field in required_fields:
            if not data.get(field):
                error_message = f"Поле {field} не заполнено."
                raise ValidationError(error_message, code=status.HTTP_400_BAD_REQUEST)

        order.full_name = data["fullName"]
        order.email = data["email"]
        order.phone = data["phone"]
        order.city = data["city"]
        order.address = data["address"]

        delivery_condition = DeliveryCondition.objects.first()
        order.delivery_condition_name = delivery_condition.name
        if data["deliveryType"] == "express":
            order.delivery = 2
            order.delivery_condition_is_express = delivery_condition.is_express
        else:
            order.delivery = 1
            order.delivery_condition_cost = delivery_condition.cost
        if data["paymentType"] == 'online' or None:
            order.payment = 1
        else:
            order.payment = 2

        order.delivery_condition_threshold = delivery_condition.threshold
        order.delivery_condition = delivery_condition

        order.status = 2
        order.save()

        total_cost = order.total_cost
