# order/models.py
from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product

class DeliveryCondition(models.Model):
    name = models.CharField(max_length=100, verbose_name="Условия доставки")
    description = models.TextField(blank=True, verbose_name="Описание")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость доставки", default=200)
    threshold = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Порог бесплатной доставки", default=2000)
    is_express = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Экспресс-доставка", default=500)

    class Meta:
        verbose_name = "Условие доставки"
        verbose_name_plural = "Условия доставки"

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = (
        ("1", "Оформление"),
        ("2", "Оформлен"),
        ("3", "Не оплачен"),
        ("4", "Подтверждение оплаты"),
        ("5", "Оплачен"),
        ("6", "Доставляется"),
        ("7", "Ошибка оплаты"),
    )

    DELIVERY_CHOICES = (
        (1, "Обычная доставка"),
        (2, "Экспресс доставка"),
    )

    PAYMENT_CHOICES = (
        (1, "Онлайн картой"),
        (2, "Онлайн со случайного чужого счета"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="покупатель")
    full_name = models.CharField(max_length=150, null=True, verbose_name="ФИО")
    email = models.EmailField(null=True, verbose_name="email")
    phone_number = models.CharField(max_length=10, null=True, verbose_name="телефон")
    data_created = models.DateTimeField(auto_now_add=True, verbose_name="дата оформления")
    delivery = models.IntegerField(choices=DELIVERY_CHOICES, null=True, verbose_name="тип доставки")
    payment = models.IntegerField(choices=PAYMENT_CHOICES, null=True, verbose_name="оплата")
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=1, verbose_name="cтатус")
    city = models.CharField(max_length=150, null=True, verbose_name="город")
    address = models.CharField(max_length=300, null=True, verbose_name="адрес")

    delivery_condition_name = models.CharField(max_length=100, null=True, verbose_name="Условия доставки на момент заказа")
    delivery_condition_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name="Стоимость доставки на момент заказа", default=0)
    delivery_condition_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name="Порог бесплатной доставки на момент заказа", default=0)
    delivery_condition_is_express = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name="Экспресс-доставка на момент заказа", default=0)

    delivery_condition = models.ForeignKey(DeliveryCondition, on_delete=models.CASCADE, null=True, verbose_name="Условие доставки")

    @property
    def total_cost(self) -> float:
        total = sum((product.current_price * product.count) for product in self.products.all())
        delivery_condition = self.delivery_condition
        if delivery_condition:
            if self.delivery_condition_is_express > 0:
                delivery_cost = self.delivery_condition_is_express
            elif total < self.delivery_condition_threshold:
                delivery_cost = self.delivery_condition_cost
            else:
                delivery_cost = 0
        else:
            delivery_cost = 0
        return total + delivery_cost

    class Meta:
        db_table = "orders"
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-data_created"]

    def __str__(self) -> str:
        return f"Заказ №{self.id}"

class PurchasedProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="products", verbose_name="номер заказа")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="товар")
    count = models.PositiveIntegerField(verbose_name="кол-во")
    current_price = models.PositiveIntegerField(verbose_name="цена")
    product_count = models.PositiveIntegerField(verbose_name="кол-во товара на складе", default=0)

    class Meta:
        db_table = "purchased_products"
        verbose_name = "товар в заказе"
        verbose_name_plural = "товары в заказе"

    def __str__(self) -> str:
        return self.product.title