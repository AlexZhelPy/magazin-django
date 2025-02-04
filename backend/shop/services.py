import json
import logging
from typing import List,Dict
from django.db.models import Q

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import QuerySet, Count, Avg
from django.http import HttpRequest, Http404, JsonResponse

from rest_framework import status

from .models import Basket, Product, Category, Review, Order, PurchasedProduct, DeliveryCondition

logger = logging.getLogger(__name__)


class ProductService:
    """
    Сервис для вывода товаров
    """

    @staticmethod
    def get_product(product_id: int) -> Product | None:
        """
        Возврат товара по id
        """
        logger.debug(f"Поиск товара по id: {product_id}")

        try:
            return Product.objects.get(id=product_id)

        except ObjectDoesNotExist:
            logger.error("Товар не найден")
            raise Http404


class BasketService:
    """
    Сервис для добавления, удаления и вывода товаров из корзины авторизованного пользователя.
    """

    @classmethod
    def get_basket(cls, request: HttpRequest) -> QuerySet:
        """
        Получение записей о товарах в корзине пользователя
        """
        logger.debug("Вывод корзины авторизованного пользователя")
        user = request.user

        # Получаем товары из кэша / добавляем в кэш
        basket = cache.get_or_set(
            f"basket_{user.id}",
            Basket.objects.filter(user=user),
        )
        return basket

    @classmethod
    def add(cls, request: HttpRequest) -> QuerySet:
        """
        Добавление товара в корзину
        """
        data = request.data
        user = request.user
        logger.debug("Добавление товара в корзину авторизованного пользователя")

        try:
            basket = Basket.objects.get(user=user, product_id=data["id"])
            basket.count += data["count"]
            basket.save()
            logger.info("Увеличение кол-ва товара в корзине")

        except ObjectDoesNotExist:
            Basket.objects.create(user=user, product_id=data["id"], count=data["count"])
            logger.info("Новый товар добавлен в корзину")

        finally:
            cache.delete(
                f"basket_{user.id}"
            )  # Очистка кэша c данными о товарах в корзине пользователя
            return cls.get_basket(request)  # Возвращаем обновленную корзину с товарами

    @classmethod
    def delete(cls, request: HttpRequest) -> QuerySet:
        """
        Удаление товара из корзины
        """
        data = json.loads(request.body)

        logger.debug("Удаление товара из корзины авторизованного пользователя")
        basket = Basket.objects.get(product_id=data["id"])
        basket.count -= data["count"]

        if basket.count > 0:
            basket.save()
            logger.info("Кол-во товара уменьшено")
        else:
            logger.warning("Кол-во товара в корзине <= 0. Удаление товара из корзины")
            basket.delete()

        cache.delete(
            f"basket_{request.user.id}"
        )  # Очистка кэша c данными о товарах в корзине пользователя
        return cls.get_basket(request)  # Возвращаем обновленную корзину с товарами

    @classmethod
    def merger(cls, request: HttpRequest, user: User) -> None:
        """
        Объединение корзин при регистрации и авторизации пользователя
        """
        logger.debug("Объединение корзин")

        records = request.session.get("basket", False)
        new_records = []

        if records:
            logger.debug(f"Имеются данные для слияния: {records}")

            for prod_id, count in records.items():
                # Проверка, есть ли товар уже в корзине зарегистрированного пользователя
                try:
                    deferred_product = Basket.objects.get(user=user, product_id=prod_id)
                    deferred_product.count += count  # Суммируем кол-во товара
                    deferred_product.save(update_fields=["count"])
                    logger.debug("Кол-во товара увеличено")

                except ObjectDoesNotExist:
                    deferred_product = Basket.objects.create(
                        user=user, product_id=prod_id, count=count
                    )

                    new_records.append(deferred_product)
                    logger.debug("Новый товар добавлен в корзину")

            logger.info("Корзины объединены")

            del request.session["basket"]  # Удаляем записи из сессии
            request.session.save()

            cache.delete(
                f"basket_{request.user.id}"
            )  # Очистка кэша c данными о товарах в корзине пользователя

        else:
            logger.warning("Нет записей для слияния")

    @classmethod
    def clear(cls, user: User) -> None:
        """
        Очистка корзины (при оформлении заказа)
        """
        Basket.objects.filter(user=user).delete()
        cache.delete(
            f"basket_{user.id}"
        )  # Очистка кэша c данными о товарах в корзине пользователя
        logger.info("Корзина очищена")


class BasketSessionService:
    """
    Сервис для добавления, удаления и вывода товаров из корзины неавторизованного пользователя.
    Сохранение данных в сессии.
    """

    @classmethod
    def get_basket(cls, request: HttpRequest) -> List:
        """
        Получение записей о товарах в корзине пользователя
        """
        logger.debug("Вывод корзины гостя")

        records_list = []
        session_key = request.session.session_key
        cart_cache_key = f"basket_{session_key}"

        if cart_cache_key not in cache:
            logger.warning("Нет данных в кэше")
            products = request.session.get("basket", False)

            if products:
                logger.debug(f"Корзина пользователя: {products}")

                for prod_id, count in products.items():
                    records_list.append(
                        Basket(
                            product=Product.objects.get(id=prod_id),
                            count=count,
                        )
                    )

                cache.set(cart_cache_key, records_list)
                logger.info("Товары сохранены в кэш")

            else:
                logger.warning("Записи о товарах не найдены")
        else:
            records_list = cache.get(cart_cache_key)

        return records_list

    @classmethod
    def add(cls, request: HttpRequest) -> List:
        """
        Добавление товара в корзину гостя
        """
        logger.debug("Добавление товара в корзину гостя")

        product_id = str(request.data["id"])
        count = int(request.data["count"])
        cls.check_key(request)  # Проверка ключа в сессии

        record = request.session["basket"].get(product_id, False)

        if record:
            request.session["basket"][product_id] += count
            logger.info("Кол-во товара увеличено")
        else:
            request.session["basket"][product_id] = count
            logger.info("Новый товар добавлен")

        request.session.save()
        cls.clear_cache_cart(request=request)  # Очистка кэша с товарами корзины

        return cls.get_basket(request)  # Возврат всех товаров в корзине

    @classmethod
    def delete(cls, request: HttpRequest) -> List:
        """
        Удаление товара из корзины гостя
        """
        logger.debug("Удаление товара из корзины гостя")

        data = json.loads(request.body)
        product_id = str(data["id"])
        count = data["count"]
        count_record = request.session["basket"].get(product_id, None)

        if not count_record:
            logger.error(f"Не найден ключ в сессии")
        else:
            count_record -= count

            if count_record <= 0:
                del request.session["basket"][product_id]
                logger.info("Товар удален из сессии")
            else:
                request.session["basket"][product_id] = count_record

            request.session.save()
            cls.clear_cache_cart(request=request)  # Очистка кэша с товарами корзины

        return cls.get_basket(request)  # Возврат всех товаров в корзине

    @classmethod
    def check_key(cls, request: HttpRequest) -> None:
        """
        Проверка ключа в объекте сессии (создание при необходимости) для записи, чтения и удаления товаров
        """
        logger.debug("Проверка ключа в объекте сессии")

        if not request.session.get("basket", False):
            request.session["basket"] = {}
            logger.info("Ключ создан")

    @classmethod
    def clear_cache_cart(cls, request: HttpRequest) -> None:
        """
        Очистка кэша с товарами в сессии
        """
        session_key = request.session.session_key
        cart_cache_key = f"basket_{session_key}"

        if cache.delete(cart_cache_key):
            logger.info("Кэш с товарами успешно очищен")
        else:
            logger.error("Кэш с товарами не очищен")


class CatalogService:
    """
    Сервис для вывода каталога с товарами.
    Фильтрация и сортировка товаров по переданным параметрам.
    """

    @classmethod
    def get_products(cls, query_params: Dict, tags: List = None):
        logger.debug(f"Вывод товаров по параметрам: {query_params}")
        category_id = query_params.get("category", None)
        if category_id:
            products = cls.by_category(category_id=int(category_id))

        else:
            logger.debug(f"Вывод всех товаров")
            products = (
                Product.objects.select_related("category")
                .prefetch_related("tags", "images")
                .all()
            )

        name = query_params.get("filter[name]", None)

        if name:
            products = cls.by_name(name=name, products=products)

        min_price = query_params.get("filter[minPrice]", None)
        max_price = query_params.get("filter[maxPrice]", None)

        if min_price or max_price:
            products = cls.by_price(
                products=products, min_price=int(min_price), max_price=int(max_price)
            )

        available = query_params.get("filter[available]", "true")

        if available == "true":
            products = cls.by_available(products=products)

        sort = query_params.get("sort", None)
        sort_type = query_params.get("sortType", "inc")

        if sort:
            products = cls.by_sort(products=products, sort=sort)

            if sort_type == "dec":
                products = products.reverse()

        if tags:
            products = cls.by_tags(products=products, tags=tags)

        free_delivery = query_params.get("filter[freeDelivery]", "false")

        if free_delivery == "true":
            products = cls.be_free_delivery(products=products)

        brands = []
        for key, value in query_params.items():
            if key.startswith("filter[brands]["):
                # Извлечение индекса из ключа
                index = key.replace("filter[brands][", "").replace("]", "")
                if index.isdigit():
                    brands.append(value)
        if brands:
            # Преобразование списка брендов в список значений
            brand_values = brands
            products = cls.by_brand(products=products, brand_values=brand_values)

        product_groups = query_params.get("filter[product_groups]", None)

        if product_groups:
            # Преобразование списка брендов в список значений
            group_values = product_groups
            products = cls.by_group(products=products, group_values=group_values)

        return products[:100]

    @classmethod
    def by_category(cls, category_id: int):
        """
        Возврат товаров по id категории
        """
        logger.debug(f"Вывод товаров категории: id - {category_id}")

        try:
            category = Category.objects.get(id=category_id)

        except ObjectDoesNotExist:
            logger.error("Категория не найдена")
            return []

        # Дочерние категории
        sub_categories = category.get_descendants(include_self=True)
        products = (
            Product.objects.select_related("category")
            .prefetch_related("tags", "images")
            .filter(category__in=sub_categories, deleted=False)
        )

        return products

    @classmethod
    def by_name(cls, name: str, products: QuerySet = None):
        """
        Поиск товаров по названию
        """
        logger.debug(f"Поиск товаров по названию: {name}")

        if not products:
            logger.debug("Поиск по всем товарам")
            products = Product.objects.all()[:100]

        res = products.filter(title__iregex=rf".*({name}).*")

        return res

    @classmethod
    def by_price(cls, products: QuerySet, min_price: int, max_price: int):
        """
        Фильтрация товаров по минимальной цене
        """
        logger.debug(
            f"Фильтрация товаров по цене: min - {min_price}, max - {max_price}"
        )
        res = products.filter(price__lte=max_price, price__gte=min_price)

        return res

    @classmethod
    def be_free_delivery(cls, products: QuerySet):
        """
        Фильтрация товаров по бесплатной доставке
        """
        logger.debug(f"Фильтрация товаров по бесплатной доставке")
        res = products.filter(price__gt=DeliveryCondition.threshold)

        return res

    @classmethod
    def by_available(cls, products: QuerySet):
        """
        Фильтрация товаров по наличию
        """
        logger.debug(f"Фильтрация товаров по наличию")
        res = products.filter(count__gt=0)

        return res

    @classmethod
    def by_tags(cls, products: QuerySet, tags: List):
        """
        Фильтрация по тегам
        """
        logger.debug(f"Фильтрация товаров по тегам")
        res = list(set(products.filter(tags__in=tags)))

        return res

    @classmethod
    def by_brand(cls, products: QuerySet, brand_values: List[str]):
        """
        Фильтрация товаров по списку брендов
        """
        logger.debug(f"Фильтрация товаров по брендам: {brand_values}")
        try:
            # Создаем пустой Q объект для фильтрации
            filter_query = Q()

            # Перебираем каждый бренд и добавляем его в Q объект
            for brand in brand_values:
                filter_query |= Q(specifications__name="Бренд:", specifications__value=brand)

            # Применяем фильтрацию
            res = products.filter(filter_query)
            return res
        except Exception as e:
            logger.error(f"Ошибка при фильтрации по брендам: {e}")
            return res

    @classmethod
    def by_group(cls, products: QuerySet, group_values: List[str]):
        """
        Фильтрация товаров по списку товарных групп
        """
        logger.debug(f"Фильтрация товаров по товарным группам: {group_values}")
        try:
            res = products.filter(specifications__name="Товарная группа:", specifications__value=group_values)
            return res
        except Exception as e:
            logger.error(f"Ошибка при фильтрации по товарным группам: {e}")
            return res

    @classmethod
    def by_sort(cls, products: QuerySet, sort: str):
        """
        Сортировка товара: по цене, средней оценке, кол-ву отзывов, дате
        """
        if sort == "price":
            logger.debug("Сортировка по цене")
            return products.order_by("-price")

        elif sort == "rating":
            logger.debug("Сортировка по количеству покупок товара")
            products = products.order_by("-sold_goods")
            return products

        elif sort == "reviews":
            logger.debug("Сортировка по кол-ву отзывов")
            products = products.annotate(count_comments=Count("reviews")).order_by(
                "-count_comments"
            )
            return products

        elif sort == "date":
            logger.debug("Сортировка по дате добавления товара")
            return products.order_by("-date")


class CommentsService:
    """
    Сервис для добавления комментариев к товару
    """

    @staticmethod
    def all_comments(product_id: int) -> QuerySet:
        """
        Вывод всех (активных) комментариев к товару
        """
        logger.debug("Вывод комментариев к товару")
        comments = cache.get_or_set(
            f"comments_{product_id}",
            Review.objects.filter(product__id=product_id, deleted=False),
        )

        return comments

    @staticmethod
    def add_new_comments(product_id: int, user: User, data: Dict) -> None:
        """
        Метод для добавления нового комментария к товару
        """
        logger.debug(f"Добавление комментария к товару")

        product = ProductService.get_product(product_id=product_id)
        author = data.get("author", None)
        email = data.get("email", None)

        if not author:
            if user.last_name or user.first_name:
                author = f"{user.last_name} {user.first_name}"
            else:
                author = user.username

        if not email:
            email = user.email

        Review.objects.create(
            user=user,
            product=product,
            author=author,
            email=email,
            text=data["text"],
            rate=data["rate"],
        )

        logger.info("Комментарий успешно создан")

        cache.delete(
            f"average_rating_{product_id}"
        )  # Очистка кэша с средней оценкой товара
        cache.delete(
            f"comments_{product_id}"
        )  # Очистка кэша с комментариями к текущему товару


class OrderService:
    """
    Сервис для оформления и вывода данных о заказах
    """

    @classmethod
    def get(cls, order_id: int):
        """
        Поиск и возврат заказа по id
        """
        try:
            return Order.objects.get(id=order_id)

        except ObjectDoesNotExist:
            logger.error("Заказ не найден")
            raise Http404

    @classmethod
    def create(cls, data: List[Basket], user: User) -> int:
        """
        Создание заказа
        """
        logger.debug("Создание заказа")

        order = Order.objects.create(user=user)
        new_records = []

        for product in data:
            product = dict(product)
            if product["count"] > product["product_count"]:
                product["count"] = product["product_count"]
            record = PurchasedProduct(
                order=order,
                product_id=product["product"]["id"],
                count=product["count"],
                current_price=product["current_price"],
            )
            new_records.append(record)
        PurchasedProduct.objects.bulk_create(new_records)
        BasketService.clear(user)  # Очистка корзины

        return order.id

    @classmethod
    def update(cls, data: Dict) -> None:
        """
        Подтверждение заказа (обновление введенных данных)
        """
        order = cls.get(order_id=data["orderId"])

        all_users = User.objects.all()
        all_emails = {user.email: user for user in all_users}

        # Проверить на совпадение email
        if data["email"] in all_emails:
            # Сравнить пользователей
            user_from_db = all_emails[data["email"]]
            if order.user != user_from_db:
                error_message = f"Пользователь из заказа не совпадает с пользователем, которому принадлежит email {data['email']}"
                raise ValidationError(error_message, code=status.HTTP_400_BAD_REQUEST)
        else:
            # Записать введенный email текущему пользователю
            order.user.email = data["email"]
            order.user.save()

        # Проверка на пустые поля
        required_fields = ["fullName", "email", "phone", "city", "address"]
        for field in required_fields:
            if not data.get(field):
                error_message = f"Поле {field} не заполнено."
                raise ValidationError(error_message, code=status.HTTP_400_BAD_REQUEST)

        order.full_name = data["fullName"]
        order.email = data["email"]
        order.phone = data["phone"]
        order.city = data["city"]
        order.address = data["address"]

        delivery_condition = DeliveryCondition.objects.first()
        order.delivery_condition_name = delivery_condition.name
        if data["deliveryType"] == "express":
            order.delivery = 2
            order.delivery_condition_is_express = delivery_condition.is_express
        else:
            order.delivery = 1
            order.delivery_condition_cost = delivery_condition.cost
        if data["paymentType"] == 'online' or None:
            order.payment = 1
        else:
            order.payment = 2

        order.delivery_condition_threshold = delivery_condition.threshold
        order.delivery_condition = delivery_condition

        order.status = 2
        order.save()

        total_cost = order.total_cost
