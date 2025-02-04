# catalog/serializers.py
from rest_framework import serializers
from catalog.models import Tag, Category, Product, Specification, Review, SaleItem

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]

class ImageSerializer(serializers.Serializer):
    src = serializers.CharField()
    alt = serializers.CharField(max_length=250, default="")

    class Meta:
        fields = ["src", "alt"]

class SubCategorySerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = Category
        fields = ["id", "title", "image"]

class CategorySerializer(SubCategorySerializer):
    subcategories = SubCategorySerializer(many=True)

    class Meta:
        model = Category
        fields = ["id", "title", "image", "subcategories"]

class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ["name", "value"]

class ReviewInSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["author", "email", "text", "date", "rate"]

class ReviewOutSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField("get_author")
    email = serializers.SerializerMethodField("get_email")
    date = serializers.SerializerMethodField("date_format")

    def date_format(self, obj):
        return obj.date.strftime("%Y-%m-%d %H:%M")

    def get_author(self, obj) -> str:
        if not obj.author:
            last_name = obj.user.last_name
            first_name = obj.user.first_name
            if last_name or first_name:
                return f"{last_name} {first_name}"
            return obj.user.username
        return obj.author

    def get_email(self, obj) -> str:
        if not obj.email:
            return obj.user.email
        return obj.email

    class Meta:
        model = Review
        fields = ["author", "email", "text", "rate", "date"]

class ProductShortSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField("date_format")
    description = serializers.CharField(source="short_description")
    images = ImageSerializer(many=True)
    current_price = serializers.FloatField()
    tags = TagSerializer(many=True)
    reviews = serializers.IntegerField(source="reviews_count")
    rating = serializers.FloatField(source="average_rating")
    specifications = SpecificationSerializer(many=True)

    def date_format(self, obj):
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
    fullDescription = serializers.CharField(source="description")
    reviews = serializers.SerializerMethodField()

    def get_reviews(self, obj):
        return ReviewOutSerializer(obj.reviews.filter(deleted=False), many=True).data

    class Meta:
        model = Product
        fields = "__all__"

class CatalogSerializer(serializers.Serializer):
    currentPage = serializers.IntegerField()
    lastPage = serializers.IntegerField()
    items = ProductShortSerializer(many=True)

    class Meta:
        fields = "__all__"

class SaleItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="product.id")
    price = serializers.IntegerField(source="product.price")
    salePrice = serializers.FloatField(source="sale_price")
    dateFrom = serializers.SerializerMethodField("date_from_format")
    dateTo = serializers.SerializerMethodField("date_to_format")
    title = serializers.CharField(source="product.title")
    images = serializers.SerializerMethodField("get_images")

    def date_from_format(self, obj):
        return obj.date_from.strftime("%d-%m-%Y")

    def date_to_format(self, obj):
        return obj.date_to.strftime("%d-%m-%Y")

    def get_images(self, obj):
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

class SalesSerializer(serializers.Serializer):
    currentPage = serializers.IntegerField()
    lastPage = serializers.IntegerField()
    items = SaleItemSerializer(many=True)

    class Meta:
        fields = "__all__"