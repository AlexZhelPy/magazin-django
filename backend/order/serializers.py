# order/serializers.py
from rest_framework import serializers
from order.models import Order
from basket.serializers import BasketSerializer

class OrderIdSerializer(serializers.Serializer):
    orderId = serializers.IntegerField()

    class Meta:
        fields = ["orderId"]

class OrderSerializer(serializers.ModelSerializer):
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
        return obj.data_created.strftime("%Y-%m-%d %H:%M")

    def get_status(self, obj):
        return dict(Order.STATUS_CHOICES)[obj.status]

    def get_deliveryType(self, obj):
        if obj.delivery is not None:
            return dict(Order.DELIVERY_CHOICES)[obj.delivery]

    def get_paymentType(self, obj):
        if obj.payment is not None:
            return dict(Order.PAYMENT_CHOICES)[obj.payment]

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

class PaymentSerializer(serializers.Serializer):
    number = serializers.CharField(max_length=8)
    name = serializers.CharField(max_length=100)
    month = serializers.CharField(max_length=2)
    year = serializers.CharField(max_length=4)
    code = serializers.CharField(max_length=3)

    def validate_number(self, value: str):
        if not value.isdigit() or value[-1] == '0' or len(value) % 2 != 0:
            raise serializers.ValidationError("Введен некорректный номер карты")
        return value

    def validate_month(self, value: str):
        if not value.isdigit() or int(value) > 12 or int(value) < 1:
            raise serializers.ValidationError("Номер месяца введен некорректно")
        return value

    def validate_year(self, value: str):
        if not value.isdigit() or int(value) > 3000 or int(value) < 2000:
            raise serializers.ValidationError("Введен некорректный год")
        return value

    def validate_code(self, value: str):
        if not value.isdigit():
            raise serializers.ValidationError("Введен некорректный код")
        return value

    class Meta:
        fields = "__all__"