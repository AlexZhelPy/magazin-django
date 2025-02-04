# Generated by Django 5.0.7 on 2025-02-03 21:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Условия доставки')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('cost', models.DecimalField(decimal_places=2, default=200, max_digits=10, verbose_name='Стоимость доставки')),
                ('threshold', models.DecimalField(decimal_places=2, default=2000, max_digits=10, verbose_name='Порог бесплатной доставки')),
                ('is_express', models.DecimalField(decimal_places=2, default=500, max_digits=10, verbose_name='Экспресс-доставка')),
            ],
            options={
                'verbose_name': 'Условие доставки',
                'verbose_name_plural': 'Условия доставки',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, null=True, verbose_name='ФИО')),
                ('email', models.EmailField(max_length=254, null=True, verbose_name='email')),
                ('phone_number', models.CharField(max_length=10, null=True, verbose_name='телефон')),
                ('data_created', models.DateTimeField(auto_now_add=True, verbose_name='дата оформления')),
                ('delivery', models.IntegerField(choices=[(1, 'Обычная доставка'), (2, 'Экспресс доставка')], null=True, verbose_name='тип доставки')),
                ('payment', models.IntegerField(choices=[(1, 'Онлайн картой'), (2, 'Онлайн со случайного чужого счета')], null=True, verbose_name='оплата')),
                ('status', models.CharField(choices=[('1', 'Оформление'), ('2', 'Оформлен'), ('3', 'Не оплачен'), ('4', 'Подтверждение оплаты'), ('5', 'Оплачен'), ('6', 'Доставляется'), ('7', 'Ошибка оплаты')], default=1, max_length=1, verbose_name='cтатус')),
                ('city', models.CharField(max_length=150, null=True, verbose_name='город')),
                ('address', models.CharField(max_length=300, null=True, verbose_name='адрес')),
                ('delivery_condition_name', models.CharField(max_length=100, null=True, verbose_name='Условия доставки на момент заказа')),
                ('delivery_condition_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, verbose_name='Стоимость доставки на момент заказа')),
                ('delivery_condition_threshold', models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, verbose_name='Порог бесплатной доставки на момент заказа')),
                ('delivery_condition_is_express', models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, verbose_name='Экспресс-доставка на момент заказа')),
                ('delivery_condition', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='order.deliverycondition', verbose_name='Условие доставки')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='покупатель')),
            ],
            options={
                'verbose_name': 'заказ',
                'verbose_name_plural': 'заказы',
                'db_table': 'orders',
                'ordering': ['-data_created'],
            },
        ),
        migrations.CreateModel(
            name='PurchasedProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField(verbose_name='кол-во')),
                ('current_price', models.PositiveIntegerField(verbose_name='цена')),
                ('product_count', models.PositiveIntegerField(default=0, verbose_name='кол-во товара на складе')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='order.order', verbose_name='номер заказа')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='catalog.product', verbose_name='товар')),
            ],
            options={
                'verbose_name': 'товар в заказе',
                'verbose_name_plural': 'товары в заказе',
                'db_table': 'purchased_products',
            },
        ),
    ]
