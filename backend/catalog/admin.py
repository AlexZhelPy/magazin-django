# catalog/admin.py
from django.contrib import admin, messages
from mptt.admin import DraggableMPTTAdmin

from .models import (
    Product,
    Category,
    ImageForCategory,
    ImageForProduct,
    Review,
    Specification,
    Tag,
    SaleItem,
)
from utils.soft_remove import soft_remove_child_records

@admin.action(description="Мягкое удаление всех записей (включая дочерние)")
def deleted_all_records(queryset):
    soft_remove_child_records(queryset)
    queryset.update(deleted=True)

@admin.action(description="Мягкое удаление")
def deleted_records(queryset):
    queryset.update(deleted=True)

@admin.action(description="Восстановить записи")
def restore_records(queryset):
    queryset.update(deleted=False)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "deleted"]
    list_display_links = ("name",)
    list_editable = ("deleted",)
    actions = (deleted_records, restore_records)
    fieldsets = (("Основное", {"fields": ("name", "deleted")}),)

class ChoiceImagesForCategory(admin.TabularInline):
    model = ImageForCategory
    extra = 1

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "id", "deleted")
    list_display_links = ("indented_title",)
    list_filter = ("deleted",)
    list_editable = ("deleted",)
    search_fields = ("title",)
    inlines = (ChoiceImagesForCategory,)
    actions = (deleted_all_records, restore_records)
    fieldsets = (
        ("Основное", {"fields": ("title", "parent")}),
        ("Статусы", {"fields": ("deleted",)}),
    )

    def save_model(self, request, obj, form, change):
        if obj.parent:
            max_indent = 2
            lvl = obj.parent.level + 1
            if lvl < max_indent:
                super().save_model(request, obj, form, change)
            else:
                messages.set_level(request, messages.ERROR)
                messages.add_message(
                    request,
                    level=messages.ERROR,
                    message=f"Превышена максимальная вложенность категорий в {max_indent} уровня! Текущая вложенность: {lvl + 1}",
                )
        else:
            super().save_model(request, obj, form, change)

@admin.register(Review)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ("product", "author", "short_review", "date", "deleted")
    list_filter = ("deleted",)
    search_fields = ("product", "short_review")
    list_editable = ("deleted",)
    actions = (deleted_records, restore_records)

    def short_review(self, obj):
        if len(obj.text) > 250:
            return f"{obj.text[0:250]}..."
        return obj.text

    short_review.short_description = "Отзыв"

@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "value"]
    list_display_links = ("name",)

class ChoiceSpecifications(admin.TabularInline):
    model = Specification
    extra = 1

class ChoiceReviews(admin.TabularInline):
    model = Review
    extra = 0

class ChoiceImages(admin.TabularInline):
    model = ImageForProduct
    extra = 0

class ChoiceSales(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_name",
        "category",
        "price",
        "count",
        "limited_series",
        "sold_goods",
        "date",
        "deleted",
    )
    list_display_links = ("short_name",)
    list_filter = ("category", "tags")
    search_fields = ("title",)
    list_editable = ("deleted",)
    actions = (deleted_records, restore_records)
    inlines = (ChoiceSales, ChoiceReviews, ChoiceSpecifications, ChoiceImages)
    fieldsets = (
        ("Основное", {"fields": ("title", "short_description", "description")}),
        ("Категория и теги", {"fields": ("category", "tags")}),
        ("Стоимость", {"fields": ("price",)}),
        ("Кол-во товара", {"fields": ("count",)}),
        ("Кол-во проданного товара", {"fields": ("sold_goods",)}),
        ("Лимитированный товар", {"fields": ("limited_series",)}),
        ("Статус", {"fields": ("deleted",)}),
    )

    def short_name(self, obj):
        if len(obj.title) > 150:
            return f"{obj.title[0:150]}..."
        return obj.title

    short_name.short_description = "Название товара"

@admin.register(SaleItem)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_name",
        "sale_price",
        "discount",
        "date_from",
        "date_to",
        "deleted",
    )
    list_display_links = ("product_name",)
    search_fields = ("product_name",)
    list_editable = ("deleted",)
    actions = (deleted_records, restore_records)

    def product_name(self, obj):
        return obj.product.title[:150]

    product_name.short_description = "Товар"

    def discount(self, obj):
        return obj.discount

    discount.short_description = " Скидка"
