from django.urls import path, include
from rest_framework import routers

from .tag_view import TagListView

from .product_view import (
    ProductDetailView,
    ReviewCreateView,
)

from .catalog_view import (
    CategoriesListView,
    LimitedProductsView,
    BannersProductsView,
    PopularProductsView,
    SalesView,
    CatalogView,
)

from .basket_view import BasketView
from .order_view import OrderView, OrderDetailView
from .payment_view import PaymentView


urlpatterns = [
    path("categories/", CategoriesListView.as_view(), name="categories"),
    path(
        "product/",
        include(
            [
                path("<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
                path(
                    "<int:pk>/reviews",
                    ReviewCreateView.as_view(),
                    name="create-review",
                ),
            ]
        ),
    ),
    path("basket", BasketView.as_view(), name="basket"),
    path("orders", OrderView.as_view(), name="orders"),
    path("orders/<int:pk>", OrderDetailView.as_view(), name="orders"),
    path("payment/<int:pk>", PaymentView.as_view(), name="payment"),
    path("paymentsomeone/<int:pk>", PaymentView.as_view(), name="paymentsomeone"),
]


router = routers.SimpleRouter()
# ВАЖНО: т.к. в представлениях нет queryset / get_queryset(), то basename обязательно!
router.register(r"products/limited", LimitedProductsView, basename="limited-products")
router.register(r"banners", BannersProductsView, basename="banner")
router.register(r"products/popular", PopularProductsView, basename="popular-products")
router.register(r"sales", SalesView, basename="sales")
router.register(r"catalog", CatalogView, basename="catalog")
router.register(r"tags", TagListView, basename="tags")

urlpatterns += router.urls