# catalog/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.core.cache import cache
from mptt.models import MPTTModel, TreeForeignKey

from utils.status import STATUS_CHOICES
from utils.save_img import save_img_for_product, save_img_for_category
from utils.validates import validate_sale_price, validate_date_to

class Tag(models.Model):
    name = models.CharField(max_length=100, verbose_name="тег")
    deleted = models.BooleanField(choices=STATUS_CHOICES, default=False, verbose_name="статус")

    class Meta:
        db_table = "tags"
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name

class Category(MPTTModel):
    title = models.CharField(max_length=100, verbose_name="название")
    tags = models.ManyToManyField("Tag", related_name="categories", verbose_name="теги")
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="subcategories", verbose_name="родительская категория")
    deleted = models.BooleanField(choices=STATUS_CHOICES, default=False, verbose_name="статус")

    class MPTTMeta:
        order_insertion_by = ("title",)

    class Meta:
        db_table = "categories"
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self) -> str:
        return self.title

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="категория")
    price = models.FloatField(validators=[MinValueValidator(0)], verbose_name="цена")
    count = models.PositiveIntegerField(default=0, verbose_name="кол-во")
    date = models.DateTimeField(auto_now_add=True, verbose_name="время добавления")
    title = models.CharField(max_length=250, verbose_name="название")
    short_description = models.CharField(max_length=500, verbose_name="краткое описание")
    description = models.TextField(max_length=1000, verbose_name="описание")
    tags = models.ManyToManyField(Tag, related_name="products", verbose_name="теги")
    deleted = models.BooleanField(choices=STATUS_CHOICES, default=False, verbose_name="Статус")
    limited_series = models.BooleanField(default=False, verbose_name="Ограниченная серия")
    sold_goods = models.PositiveIntegerField(default=0, verbose_name="продано")

    @property
    def current_price(self):
        try:
            sale_item = self.saleitem
            if sale_item and not sale_item.deleted and sale_item.date_from <= timezone.now() <= sale_item.date_to:
                return sale_item.sale_price
        except SaleItem.DoesNotExist:
            pass
        return self.price

    @property
    def reviews_count(self) -> int:
        return self.reviews.count()

    @property
    def average_rating(self) -> int:
        res = cache.get_or_set(f"average_rating_{self.id}", Review.objects.filter(product_id=self.id).aggregate(average_rate=Avg("rate")))
        try:
            return round(res["average_rate"], 1)
        except TypeError:
            return 0

    class Meta:
        db_table = "products"
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["id"]

    def add_tags(self, *args, **kwargs):
        chair_tags = self.category.tags.all()
        for tag in self.tags.all():
            if tag not in chair_tags:
                self.category.tags.add(tag)
        super(Product, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            self.add_tags()
        except ValueError:
            super(Product, self).save(*args, **kwargs)
            self.add_tags()
        if cache.delete(f"product_{self.id}"):
            logger.info("Кэш товара очищен")

    def __str__(self) -> str:
        return str(self.title)

class ImageForProduct(models.Model):
    path = models.ImageField(upload_to=save_img_for_product, verbose_name="изображение")
    alt = models.CharField(max_length=250, verbose_name="alt")
    product = models.ForeignKey("Product", on_delete=models.CASCADE, verbose_name="товар", related_name="images")

    class Meta:
        db_table = "images_for_products"
        verbose_name = "изображение"
        verbose_name_plural = "изображения"

    @property
    def src(self) -> str:
        return f"/media/{self.path}"

    def __str__(self) -> str:
        return str(self.path)

class ImageForCategory(models.Model):
    path = models.ImageField(upload_to=save_img_for_category, verbose_name="изображение")
    alt = models.CharField(max_length=250, verbose_name="alt")
    category = models.OneToOneField("Category", on_delete=models.CASCADE, verbose_name="категория", related_name="image")

    class Meta:
        db_table = "images_for_category"
        verbose_name = "изображение"
        verbose_name_plural = "изображения"

    @property
    def src(self) -> str:
        return f"/media/{self.path}"

    def __str__(self) -> str:
        return str(self.path)

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="пользователь")
    product = models.ForeignKey("Product", on_delete=models.CASCADE, verbose_name="товар", related_name="reviews")
    author = models.CharField(max_length=150, blank=True, null=True, verbose_name="автор")
    email = models.EmailField(blank=True, null=True, verbose_name="email")
    text = models.TextField(max_length=2000, verbose_name="отзыв")
    rate = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="оценка")
    date = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(choices=STATUS_CHOICES, default=False, verbose_name="Статус")

    class Meta:
        db_table = "reviews"
        verbose_name = "отзыв"
        verbose_name_plural = "отзывы"
        ordering = ["-date"]

    def __str__(self) -> str:
        return str(self.author)

class SaleItem(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, verbose_name="товар")
    sale_price = models.FloatField(verbose_name="цена со скидкой")
    date_from = models.DateTimeField(verbose_name="дата начала распродажи")
    date_to = models.DateTimeField(verbose_name="дата окончания распродажи")
    deleted = models.BooleanField(choices=STATUS_CHOICES, default=False, verbose_name="Статус")

    @property
    def discount(self) -> int:
        return 100 - int((self.sale_price / self.product.price) * 100)

    class Meta:
        db_table = "sales_items"
        verbose_name = "распродажа"
        verbose_name_plural = "распродажи"
        ordering = ["-date_to"]

    def __str__(self) -> str:
        return self.product.title

    def clean(self):
        validate_date_to(self)
        validate_sale_price(self)

class Specification(models.Model):
    name = models.CharField(max_length=100, verbose_name="характеристика")
    value = models.CharField(max_length=100, verbose_name="значение")
    product = models.ForeignKey("Product", on_delete=models.CASCADE, verbose_name="товар", related_name="specifications")

    class Meta:
        db_table = "specifications"
        verbose_name = "характеристика товара"
        verbose_name_plural = "характеристики товаров"

    def __str__(self) -> str:
        return str(self.name)