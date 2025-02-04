from django.urls import path, include

from .auth import register_user, user_login, user_logout
from .profile import update_avatar, update_password, ProfileView


urlpatterns = [
    # URL-маршруты приложения
    # Регистрация, авторизация, выход из учетной записи,
    # Профиль пользователя, обновление аватара, обновление пароля
    path('sign-up/', register_user, name="sign-up"),
    path('sign-out', user_logout, name="sign-out"),
    path('sign-in', user_login, name="sign-in"),
    path('profile/', ProfileView.as_view(), name="profile"),
    path('profile/avatar/', update_avatar, name="update-profile"),
    path('profile/password/', update_password, name="update-password"),
]
