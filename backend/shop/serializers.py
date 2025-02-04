import logging

from rest_framework import serializers

from .models import Basket, Product, Category, Order, Specification, Review, SaleItem, Tag, DeliveryCondition


logger = logging.getLogger(__name__)


class TagSerializer(serializers.ModelSerializer):
    """
    Схема для тегов
    """

    class Meta:
        model = Tag
        fields = ["id", "name"]


class ImageSerializer(serializers.Serializer):
    """
    Схема для изображений
    """

    src = serializers.CharField()
    alt = serializers.CharField(max_length=250, default="")

    class Meta:
        fields = ["src", "alt"]


class BasketSerializer(serializers.Serializer):
    """
    Схема для корзины с товарами
    """

    id = serializers.IntegerField(source="product.id")
    category = serializers.IntegerField(source="product.category.id")
    current_price = serializers.FloatField()
    product_count = serializers.IntegerField()
    count = serializers.IntegerField()
    date = serializers.DateTimeField(source="product.date")
    title = serializers.CharField(source="product.title")
    description = serializers.CharField(source="product.short_description")
    images = ImageSerializer(source="product.images", many=True)
    tags = TagSerializer(source="product.tags", many=True)
    reviews = serializers.IntegerField(source="product.reviews_count")
    rating = serializers.FloatField(source="product.average_rating")
    delivery_condition = serializers.SerializerMethodField()

    def get_delivery_condition(self, obj):
        delivery_condition = DeliveryCondition.objects.first()
        return DeliveryConditionSerializer(delivery_condition).data

    class Meta:
        model = Basket
        fields = [
            "id",
            "category",
            "current_price",
            "product_count",
            "count",
            "date",
            "title",
            "description",
            "images",
            "tags",
            "reviews",
            "rating",
        ]


class DeliveryConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCondition
        fields = ['name', 'description', 'cost', 'threshold', 'is_express']


class SubCategorySerializer(serializers.ModelSerializer):
    """
    Схема для вложенной категорий товаров
    """

    image = ImageSerializer()  # Вложенная схема с изображением

    class Meta:
        model = Category
        fields = ["id", "title", "image"]


class CategorySerializer(SubCategorySerializer):
    """
    Схема для категорий товаров
    """

    subcategories = SubCategorySerializer(
        many=True
    )  # Вложенная схема (подкатегория товаров)

    class Meta:
        model = Category
        fields = ["id", "title", "image", "subcategories"]


class OrderIdSerializer(serializers.Serializer):
    """
    Схема для вывода id заказа
    """

    orderId = serializers.IntegerField()

    class Meta:
        fields = ["orderId"]


class OrderSerializer(serializers.ModelSerializer):
    """
    Схема для оформления заказа
    """

    createdAt = serializers.SerializerMethodField("date_format")
    fullName = serializers.CharField(source="user.profile.full_name")
    email = serializers.CharField(source="user.email")
    phone = serializers.CharField(source="user.profile.phone")
    totalCost = serializers.FloatField(source="total_cost")
    products = BasketSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    deliveryType = serializers.SerializerMethodField()
    paymentType = serializers.SerializerMethodField()

    def date_format(self, obj):
        """
        Изменяем формат времени
        """
        return obj.data_created.strftime("%Y-%m-%d %H:%M")  # 2023-05-05 12:12

    class Meta:
        model = Order
        fields = [
            "id",
            "createdAt",
            "fullName",
            "email",
            "phone",
            "deliveryType",
            "paymentType",
            "totalCost",
            "status",
            "city",
            "address",
            "products",
        ]

    def get_status(self, obj):
        # Возвращаем словарь с номером и описанием статуса
        return dict(Order.STATUS_CHOICES)[obj.status]

    def get_deliveryType(self, obj):
        # Возвращаем словарь с номером и описанием доставки
        if obj.delivery != None:
            return dict(Order.DELIVERY_CHOICES)[obj.delivery]

    def get_paymentType(self, obj):
        # Возвращаем словарь с номером и описанием оплаты
        if obj.payment != None:
            return dict(Order.PAYMENT_CHOICES)[obj.payment]


class PaginationSerializerMixin(serializers.Serializer):
    """
    Схема добавляет поля текущей и последней страницы при разбивке результатов товаров на страницы
    """

    currentPage = serializers.IntegerField()
    lastPage = serializers.IntegerField()

    class Meta:
        fields = "__all__"


class PaymentSerializer(serializers.Serializer):
    """
    Схема для входных данных при оплате заказа
    """

    number = serializers.CharField(max_length=8)
    name = serializers.CharField(max_length=100)
    month = serializers.CharField(max_length=2)
    year = serializers.CharField(max_length=4)
    code = serializers.CharField(max_length=3)

    def validate_number(self, value: str):
        """
        Проверка, что введены цифры, не оканчивается на 0 и четный номер
        """

        if not value.isdigit() or value[-1] == '0' or len(value) % 2 != 0:
            raise serializers.ValidationError("Введен некорректный номер карты")
        return value

    def validate_month(self, value: str):
        """
        Проверка корректности номера месяца
        """
        if not value.isdigit() or int(value) > 12 or int(value) < 1:
            raise serializers.ValidationError("Номер месяца введен некорректно")
        return value

    def validate_year(self, value: str):
        """
        Проверка корректности введенного года
        """
        if not value.isdigit() or int(value) > 3000 or int(value) < 2000:
            raise serializers.ValidationError("Введен некорректный год")
        return value

    def validate_code(self, value: str):
        """
        Проверка корректности введенного кода
        """
        if not value.isdigit():
            raise serializers.ValidationError("Введен некорректный код")
        return value

    class Meta:
        fields = "__all__"


class SpecificationSerializer(serializers.ModelSerializer):
    """
    Схема для характеристик товара
    """

    class Meta:
        model = Specification
        fields = ["name", "value"]


class ReviewInSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["author", "email", "text", "date", "rate"]


class ReviewOutSerializer(serializers.ModelSerializer):
    """
    Схема для отзывов
    """

    author = serializers.SerializerMethodField("get_author")
    email = serializers.SerializerMethodField("get_email")
    date = serializers.SerializerMethodField("date_format")

    def date_format(self, obj):
        """
        Изменяем формат времени
        """
        return obj.date.strftime("%Y-%m-%d %H:%M")

    def get_author(self, obj) -> str:
        """
        Возвращаем имя автора
        """
        if not obj.author:
            last_name = obj.user.last_name
            first_name = obj.user.first_name

            if last_name or first_name:
                return f"{last_name} {first_name}"

            return obj.user.username

        else:
            return obj.author

    def get_email(self, obj) -> str:
        """
        Возвращаем email пользователя, оставившего отзыв
        """
        if not obj.email:
            return obj.user.email

        return obj.email

    class Meta:
        model = Review
        fields = [
            "author",
            "email",
            "text",
            "rate",
            "date",
        ]


class ProductShortSerializer(serializers.ModelSerializer):
    """
    Схема для товара (короткая)
    """

    date = serializers.SerializerMethodField("date_format")
    description = serializers.CharField(source="short_description")
    images = ImageSerializer(many=True)
    current_price = serializers.FloatField()
    tags = TagSerializer(many=True)
    reviews = serializers.IntegerField(source="reviews_count")
    rating = serializers.FloatField(source="average_rating")
    specifications = SpecificationSerializer(many=True)

    def date_format(self, obj):
        """
        Изменяем формат времени
        """
        return obj.date.strftime(f"%a %b %Y %H:%M:%S %Z%z")

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "current_price",
            "count",
            "date",
            "title",
            "description",
            "images",
            "tags",
            "reviews",
            "rating",
            "specifications",
        ]


class ProductFullSerializer(ProductShortSerializer):
    """
    Схема для товара (полная). Для страницы товара.
    """

    fullDescription = serializers.CharField(source="description")
    reviews = serializers.SerializerMethodField()

    def get_reviews(self, obj):
        """
        Возвращаем список отзывов, исключая удаленные
        """
        return ReviewOutSerializer(obj.reviews.filter(deleted=False), many=True).data

    class Meta:
        model = Product
        fields = "__all__"


class CatalogSerializer(PaginationSerializerMixin):
    """
    Схема для вывода каталога товаров
    """

    items = ProductShortSerializer(many=True)


class SaleItemSerializer(serializers.ModelSerializer):
    """
    Схема для записей о распродажах товаров
    """

    id = serializers.CharField(source="product.id")
    price = serializers.IntegerField(source="product.price")
    salePrice = serializers.FloatField(source="sale_price")
    dateFrom = serializers.SerializerMethodField("date_from_format")
    dateTo = serializers.SerializerMethodField("date_to_format")
    title = serializers.CharField(source="product.title")
    images = serializers.SerializerMethodField("get_images")

    def date_from_format(self, obj):
        """
        Изменяем формат времени
        """
        return obj.date_from.strftime("%d-%m-%Y")

    def date_to_format(self, obj):
        """
        Изменяем формат времени
        """
        return obj.date_to.strftime("%d-%m-%Y")

    def get_images(self, obj):
        """
        Возвращаем изображения товара
        """
        images = obj.product.images.all()
        serializer = ImageSerializer(images, many=True)

        return serializer.data

    class Meta:
        model = SaleItem
        fields = [
            "id",
            "price",
            "salePrice",
            "dateFrom",
            "dateTo",
            "title",
            "images",
        ]


class SalesSerializer(PaginationSerializerMixin):
    """
    Схема для вывода списка предложений с товарами на распродаже
    """

    items = SaleItemSerializer(many=True)



