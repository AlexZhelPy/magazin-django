import logging
from typing import List,Dict
from django.db.models import Q

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet, Count
from django.http import Http404


from catalog.models import Product, Category, Review
from order.models import DeliveryCondition

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

        return products

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
