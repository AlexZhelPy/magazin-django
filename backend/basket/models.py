# basket/models.py
from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product

class Basket(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name="покупатель")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="товар")
    count = models.PositiveIntegerField(default=1, verbose_name="кол-во")

    @property
    def current_price(self) -> int:
        current_price = int(self.product.current_price * self.count)
        return current_price

    def product_count(self) -> int:
        product_count = int(self.product.count)
        return product_count

    class Meta:
        db_table = "basket"
        verbose_name = "Корзина покупателя"
        verbose_name_plural = "Корзины покупателей"

    def __str__(self) -> str:
        return f"Корзина покупателя"