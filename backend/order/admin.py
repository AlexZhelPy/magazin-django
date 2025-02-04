# order/admin.py
from django.contrib import admin
from django.db.models import QuerySet
from .models import Order, PurchasedProduct, DeliveryCondition

class ProductsInOrder(admin.TabularInline):
    model = PurchasedProduct
    can_delete = False
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["order", "product", "count", "current_price", "product_count"]
        return self.readonly_fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "delivery_condition_name",
        "payment",
        "city",
        "data",
        "status",
        "delivery_cost_info",
    )
    list_display_links = ("id",)
    search_fields = ("id", "user__profile__full_name", "city", "address")
    list_filter = ("delivery_condition_is_express", "payment", "status")
    inlines = (ProductsInOrder,)

    def data(self, obj):
        return obj.data_created.strftime(f"%d.%m.%Y %H:%M:%S")

    data.short_description = "дата оформления"

    def full_name(self, obj):
        return obj.user.profile.full_name

    full_name.short_description = "Покупатель"

    def get_queryset(self, request) -> QuerySet:
        return Order.objects.select_related("user__profile")

    def delivery_cost_info(self, obj):
        if obj.delivery_condition_is_express:
            return f"Экспресс-доставка: {obj.delivery_condition_is_express} руб."
        elif (obj.total_cost - obj.delivery_condition_cost) < obj.delivery_condition_threshold:
            return f"Обычная доставка: {obj.delivery_condition_cost} руб."
        else:
            return "Бесплатная доставка"

    delivery_cost_info.short_description = "Стоимость доставки"

    fieldsets = (
        ("Данные о заказе", {"fields": ("payment", "status")}),
        ("Данные о покупателе и доставке", {"fields": ("full_name", "city", "address")}),
        ("Доставка", {"fields": ("delivery_cost_info",)}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                "id",
                "full_name",
                "data_created",
                "city",
                "address",
                "delivery",
                "payment",
                "status",
                "delivery_cost_info",
            ]
        return self.readonly_fields

@admin.register(DeliveryCondition)
class DeliveryConditionAdmin(admin.ModelAdmin):
    list_display = ("name", "cost", "threshold", "is_express")
    list_editable = ("cost", "threshold", "is_express")
    search_fields = ("name",)

    fieldsets = (
        ("Основное", {"fields": ("name", "description")}),
        ("Стоимость и порог", {"fields": ("cost", "threshold")}),
        ("Экспресс-доставка", {"fields": ("is_express",)}),
    )
