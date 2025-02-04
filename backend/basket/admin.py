# basket/admin.py
from django.contrib import admin
from .models import Basket

@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "count", "current_price")