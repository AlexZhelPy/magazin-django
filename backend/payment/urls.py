from django.urls import path

from .views import PaymentView


urlpatterns = [
    path("payment/<int:pk>", PaymentView.as_view(), name="payment"),
    path("paymentsomeone/<int:pk>", PaymentView.as_view(), name="paymentsomeone"),
]