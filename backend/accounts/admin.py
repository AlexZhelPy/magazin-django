from django.contrib import admin

from .models import Profile, ImageForAvatar


@admin.action(description="Мягкое удаление")
def deleted_records(adminmodel, request, queryset):
    """
        Действие для мягкого удаления записей.

        Это действие меняет статус записей на `deleted=True`

            **Параметры:**
                - `adminmodel`: Модель администратора.
                - `request`: Объект запроса Django.
                - `queryset`: Набор записей для обработки.

                **Возвращаемое значение:**
                - Нет возвращаемого значения, но обновляет записи в базе данных.
    """

    queryset.update(deleted=True)


@admin.action(description="Восстановить записи")
def restore_records(adminmodel, request, queryset):
    """
        Действие для восстановления записей, отключенных через мягкое удаление.

        Это действие меняет статус записей на `deleted=False`.

            **Параметры:**
                - `adminmodel`: Модель администратора.
                - `request`: Объект запроса Django.
                - `queryset`: Набор записей для обработки.

            **Возвращаемое значение:**
                - Нет explicit возвращаемого значения, но обновляет записи в базе данных.
    """
    queryset.update(deleted=False)


class ChoiceAvatar(admin.TabularInline):
    """
        Вывод аватара пользователя
    """

    model = ImageForAvatar
    extra = 1


@admin.register(Profile)
class TagAdmin(admin.ModelAdmin):
    """
        Админ-панель для профайлов пользователей.

        Этот класс настраивает интерфейс администратора для модели `Profile`,
        позволяя управлять данными профайлов пользователей.

            **Атрибуты:**
                - `list_display`: Список полей, отображаемых в списке записей.
                - `list_display_links`: Список полей, которые можно использовать как ссылки для редактирования записей.
                - `list_editable`: Список полей, которые можно редактировать прямо в списке записей.
                - `inlines`: Вложенные классы для отображения дополнительных данных (в данном случае аватаров).
                - `actions`: Действия, доступные в админ-панели (мягкое удаление и восстановление записей).
                - `fieldsets`: Группы полей для более удобного отображения в форме редактирования.
    """

    list_display = ["id", "username", "full_name", "email", "phone", "deleted"]
    list_display_links = ("full_name",)
    list_editable = ("deleted",)
    inlines = (ChoiceAvatar,)

    # Мягкое удаление/восстановление записей
    actions = (
        deleted_records,
        restore_records,
    )

    fieldsets = (("Основное", {"fields": ("full_name", "phone", "deleted")}),)

    def username(self, object):
        """
            Метод для отображения имени пользователя в админ-панели.

                **Параметры:**
                    - `object`: Объект профайла пользователя.

                **Возвращаемое значение:**
                    - Имя пользователя.
        """
        return object.user.username

    username.short_description = "Username"

    def email(self, object):
        """
            Метод для отображения электронной почты пользователя в админ-панели.

                **Параметры:**
                    - `object`: Объект профайла пользователя.

                **Возвращаемое значение:**
                    - Электронная почта пользователя.
        """
        return object.user.email

    email.short_description = "Email"
