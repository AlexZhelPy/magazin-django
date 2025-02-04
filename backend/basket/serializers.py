# basket/serializers.py
from rest_framework import serializers
from .models import Basket
from catalog.serializers import ImageSerializer, TagSerializer
from order.models import DeliveryCondition

class DeliveryConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryCondition
        fields = ['name', 'description', 'cost', 'threshold', 'is_express']

class BasketSerializer(serializers.Serializer):
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