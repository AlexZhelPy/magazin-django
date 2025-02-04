import logging
from datetime import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.core.cache import cache
from mptt.models import MPTTModel, TreeForeignKey

from .utils.status import STATUS_CHOICES
from .utils.save_img import save_img_for_product, save_img_for_category
from .utils.validates import validate_sale_price, validate_date_to


logger = logging.getLogger(__name__)


class Tag(models.Model):
    """
    Модель для хранения тегов для товаров
    """

    name = models.CharField(max_length=100, verbose_name="тег")
    deleted = models.BooleanField(
        choices=STATUS_CHOICES, default=False, verbose_name="статус"
    )  # Мягкое удаление

    class Meta:
        db_table = "tags"
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name


class Category(MPTTModel):
    """
    Модель для хранения данных о категориях товаров с возможностью вложенных категорий
    """

    title = models.CharField(max_length=100, verbose_name="название")
    tags = models.ManyToManyField("Tag", related_name="categories", verbose_name="теги")

    # Вложенные категории
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name="родительская категория",
    )

    # Мягкое удаление
    deleted = models.BooleanField(
        choices=STATUS_CHOICES, default=False, verbose_name="статус"
    )

    class MPTTMeta:
        """
        Сортировка по вложенности
        """

        order_insertion_by = ("title",)

    class Meta:
        db_table = "categories"
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    """
    Модель для хранения данных о товарах
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="категория",
    )
    price = models.FloatField(validators=[MinValueValidator(0)], verbose_name="цена")
    count = models.PositiveIntegerField(default=0, verbose_name="кол-во")
    date = models.DateTimeField(auto_now_add=True, verbose_name="время добавления")
    title = models.CharField(max_length=250, verbose_name="название")
    short_description = models.CharField(
        max_length=500, verbose_name="краткое описание"
    )
    description = models.TextField(max_length=1000, verbose_name="описание")
    tags = models.ManyToManyField(Tag, related_name="products", verbose_name="теги")
    deleted = models.BooleanField(
        choices=STATUS_CHOICES, default=False, verbose_name="Статус"
    )  # Мягкое удаление
    limited_series = models.BooleanField(default=False, verbose_name="Ограниченная серия")
    sold_goods = models.PositiveIntegerField(default=0, verbose_name="продано")

    @property
    def current_price(self):
        """
        Возвращает текущую цену товара, учитывая активную распродажу
        """
        try:
            sale_item = self.saleitem
            if sale_item and not sale_item.deleted and sale_item.date_from <= timezone.now() <= sale_item.date_to:
                return sale_item.sale_price
        except SaleItem.DoesNotExist:
            pass
        return self.price

    @property
    def reviews_count(self) -> int:
        """
        Кол-во отзывов у товара
        """
        return self.reviews.count()


    @property
    def average_rating(self) -> int:
        """
        Расчет средней оценки товара на основе всех отзывов
        """
        res = cache.get_or_set(
            f"average_rating_{self.id}",
            Review.objects.filter(product_id=self.id).aggregate(
                average_rate=Avg("rate")
            ),
        )

        try:
            # Округляем рейтинг товара до 1 знака после запятой
            return round(res["average_rate"], 1)
        except TypeError:
            return 0

    class Meta:
        db_table = "products"
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["id"]

    def add_tags(self, *args, **kwargs):
        """
        Добавляем запись об используемых тегах в категорию товара
        (для быстрого вывода всех тегов товаров определенной категории)
        """
        chair_tags = self.category.tags.all()

        for tag in self.tags.all():
            if tag not in chair_tags:
                self.category.tags.add(tag)

        super(Product, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Сохранение тегов и очистка кэша при сохранении и изменении товара
        """

        try:
            self.add_tags()

        except ValueError:
            super(Product, self).save(*args, **kwargs)
            self.add_tags()

        if cache.delete(f"product_{self.id}"):
            logger.info("Кэш товара очищен")

    def __str__(self) -> str:
        return str(self.title)


class Basket(models.Model):
    """
    Модель для хранения данных о корзине покупателя
    """

    # null=True - для создания экземпляра корзины для анонимного пользователя из данных сессии
    user = models.ForeignKey(
        User, null=True, on_delete=models.CASCADE, verbose_name="покупатель"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="товар")
    count = models.PositiveIntegerField(default=1, verbose_name="кол-во")

    @property
    def current_price(self) -> int:
        """
        Стоимость одной позиции товара с учетом скидки и кол-ва товара (с округлением до целого)
        """
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


class ImageForProduct(models.Model):
    """
    Модель для хранения данных об изображениях товаров
    """

    path = models.ImageField(upload_to=save_img_for_product, verbose_name="изображение")
    alt = models.CharField(max_length=250, verbose_name="alt")
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, verbose_name="товар", related_name="images"
    )

    class Meta:
        db_table = "images_for_products"
        verbose_name = "изображение"
        verbose_name_plural = "изображения"

    @property
    def src(self) -> str:
        """
        Переопределяем path для подстановки в frontend и корректного отображения картинки
        """
        return f"/media/{self.path}"

    def __str__(self) -> str:
        return str(self.path)


class ImageForCategory(models.Model):
    """
    Модель для хранения данных об изображениях для категорий товаров
    """

    path = models.ImageField(
        upload_to=save_img_for_category, verbose_name="изображение"
    )
    alt = models.CharField(max_length=250, verbose_name="alt")
    category = models.OneToOneField(
        "Category",
        on_delete=models.CASCADE,
        verbose_name="категория",
        related_name="image",
    )

    class Meta:
        db_table = "images_for_category"
        verbose_name = "изображение"
        verbose_name_plural = "изображения"

    @property
    def src(self) -> str:
        """
        Переопределяем path для подстановки в frontend и корректного отображения картинки
        """
        return f"/media/{self.path}"

    def __str__(self) -> str:
        return str(self.path)


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
    """
    Модель для хранения данных о заказах
    """

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


    # многие поля null, т.к. по фронту сначала создается заказ, после обновляется подтвержденными данными
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="покупатель")
    full_name = models.CharField(max_length=150, null=True, verbose_name="ФИО")
    email = models.EmailField(null=True, verbose_name="email")
    phone_number = models.CharField(max_length=10, null=True, verbose_name="телефон")
    data_created = models.DateTimeField(
        auto_now_add=True, verbose_name="дата оформления"
    )
    delivery = models.IntegerField(
        choices=DELIVERY_CHOICES, null=True, verbose_name="тип доставки"
    )
    payment = models.IntegerField(
        choices=PAYMENT_CHOICES, null=True, verbose_name="оплата"
    )
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default=1, verbose_name="cтатус"
    )
    city = models.CharField(max_length=150, null=True, verbose_name="город")
    address = models.CharField(max_length=300, null=True, verbose_name="адрес")

    delivery_condition_name = models.CharField(max_length=100, null=True,
                                               verbose_name="Условия доставки на момент заказа")
    delivery_condition_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                                  verbose_name="Стоимость доставки на момент заказа", default=0)
    delivery_condition_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                                       verbose_name="Порог бесплатной доставки на момент заказа", default=0)
    delivery_condition_is_express = models.DecimalField(max_digits=10, decimal_places=2, null=True,
                                                        verbose_name="Экспресс-доставка на момент заказа", default=0)

    delivery_condition = models.ForeignKey(DeliveryCondition, on_delete=models.CASCADE, null=True,
                                           verbose_name="Условие доставки")


    @property
    def total_cost(self) -> float:
        """
        Общая стоимость всех товаров в заказе
        """
        total = sum((product.current_price * product.count) for product in self.products.all())

        # Получаем выбранное условие доставки
        delivery_condition = self.delivery_condition

        if delivery_condition:
            # Расчет стоимости доставки на основе выбранного условия
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
    """
    Модель для хранения товаров, их кол-ва и стоимости на момент покупки с привязкой к номеру заказа
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="номер заказа",
    )
    # models.PROTECT - нельзя удалить, пока есть связанные ссылки
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="товар")
    count = models.PositiveIntegerField(verbose_name="кол-во")
    current_price = models.PositiveIntegerField(
        verbose_name="цена"
    )
    product_count = models.PositiveIntegerField(
        verbose_name="кол-во товара на складе", default=0
    ) # На момент оформления заказа

    class Meta:
        db_table = "purchased_products"
        verbose_name = "товар в заказе"
        verbose_name_plural = "товары в заказе"

    def __str__(self) -> str:
        return self.product.title


class Review(models.Model):
    """
    Модель для хранения данных об отзывах о товарах
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="пользователь"
    )
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        verbose_name="товар",
        related_name="reviews",
    )
    author = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="автор"
    )
    email = models.EmailField(blank=True, null=True, verbose_name="email")
    text = models.TextField(max_length=2000, verbose_name="отзыв")
    rate = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="оценка"
    )
    date = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(
        choices=STATUS_CHOICES, default=False, verbose_name="Статус"
    )  # Мягкое удаление

    class Meta:
        db_table = "reviews"
        verbose_name = "отзыв"
        verbose_name_plural = "отзывы"
        ordering = ["-date"]

    def __str__(self) -> str:
        return str(self.author)


class SaleItem(models.Model):
    """
    Модель для хранения данных о скидках на товары
    """

    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, verbose_name="товар"
    )
    sale_price = models.FloatField(verbose_name="цена со скидкой")
    date_from = models.DateTimeField(verbose_name="дата начала распродажи")
    date_to = models.DateTimeField(verbose_name="дата окончания распродажи")

    deleted = models.BooleanField(
        choices=STATUS_CHOICES, default=False, verbose_name="Статус"
    )  # Мягкое удаление

    @property
    def discount(self) -> int:
        """
        Скидка на товар
        """
        return 100 - int((self.sale_price / self.product.price) * 100)

    class Meta:
        db_table = "sales_items"
        verbose_name = "распродажа"
        verbose_name_plural = "распродажи"
        ordering = ["-date_to"]

    def __str__(self) -> str:
        return self.product.title

    def clean(self):
        """
        Проверка цены со скидкой и дат распродажи
        """
        validate_date_to(self)
        validate_sale_price(self)


class Specification(models.Model):
    """
    Модель для хранения данных о характеристиках товаров
    """

    name = models.CharField(max_length=100, verbose_name="характеристика")
    value = models.CharField(max_length=100, verbose_name="значение")
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        verbose_name="товар",
        related_name="specifications",
    )

    class Meta:
        db_table = "specifications"
        verbose_name = "характеристика товара"
        verbose_name_plural = "характеристики товаров"

    def __str__(self) -> str:
        return str(self.name)
