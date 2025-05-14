from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import ShopView, CategoryView, RegisterAccountView, UserProfileView, ProductInfoView, \
    LoginAccountView, BasketView, BasketItemView, ContactView, ConfirmOrderView, ListOrdersView, BasketItemView, ConfirmEmailView, ContactDetailView

router = DefaultRouter()
urlpatterns = [
                  path('token/', TokenObtainPairView.as_view(), ),
                  path('token/refresh/', TokenRefreshView.as_view(), ),
                  path('user/register/', RegisterAccountView.as_view()),  # Регистрация нового пользователя
                  path('user/login/', LoginAccountView.as_view()),  # Вход в систему
                  path('user/profile/', UserProfileView.as_view()),  # Информация о пользователе

                  path('shops/', ShopView.as_view()),  # Список магазинов
                  path('categories/', CategoryView.as_view()),  # Список категорий
                  path('products/', ProductInfoView.as_view()),  # Список товаров

                  path('basket/', BasketView.as_view()),  # Просмотр корзины
                  path('basket/<int:id>/', BasketItemView.as_view()),

                  path('contacts/', ContactView.as_view()),  # Контакты,Для списка и создания
                  path('contacts/<int:pk>/', ContactDetailView.as_view()),  # Для конкретного контакта
                  path('orders/confirm/', ConfirmOrderView.as_view()),  # Подтверждение заказа
                  path('orders/', ListOrdersView.as_view()),  # Список всех заказов текущего пользователя
                  path('confirm-email/<int:user_id>/', ConfirmEmailView.as_view()), # Подтверждение email

              ] + router.urls
