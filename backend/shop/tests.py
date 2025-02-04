from django.test import TestCase
from .models import Product, Category
from .serializers import ProductShortSerializer, ProductFullSerializer

class ProductSerializerTest(TestCase):
    def setUp(self):
        # Создание категории
        self.category = Category.objects.create(
            title="Test Category",
            # Другие поля, если необходимо
        )

        # Создание продукта с указанной категорией
        self.product = Product.objects.create(
            title="Test Product",
            price=100,
            count=10,
            date="2024-01-01 12:00:00",
            short_description="Short description",
            description="Full description",
            category=self.category,  # Указание категории
            # Другие поля, если необходимо
        )

    def test_product_short_serializer(self):
        serializer = ProductShortSerializer(self.product)
        self.assertEqual(serializer.data['id'], self.product.id)
        self.assertEqual(serializer.data['title'], self.product.title)
        self.assertEqual(serializer.data['price'], self.product.price)
        print('serializator id=====', serializer.data['id'])
        # Проверка других полей, если необходимо

    def test_product_full_serializer(self):
        serializer = ProductFullSerializer(self.product)
        self.assertEqual(serializer.data['id'], self.product.id)
        self.assertEqual(serializer.data['title'], self.product.title)
        self.assertEqual(serializer.data['price'], self.product.price)
        print('serializator id full=====', serializer.data['id'])
        # Проверка других полей, если необходимо
