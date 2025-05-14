from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Shop, Category, ProductInfo, Order, OrderItem, Contact, User
from .serializers import ShopSerializer, CategorySerializer, UserRegisterSerializer, UserProfileSerializer, \
    ProductInfoSerializer, MyTokenObtainPairSerializer, OrderSerializer, OrderItemSerializer, ContactSerializer
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class LoginAccountView(TokenObtainPairView):
    """
    Класс для аутентификации пользователей.
    Возвращает JWT-токены при успешной аутентификации.
    """
    serializer_class = MyTokenObtainPairSerializer


class RegisterAccountView(generics.CreateAPIView):
    """
    Класс для регистрации новых пользователей.
    Отправляет email с подтверждением после успешной регистрации.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает POST-запрос на регистрацию пользователя.

        Параметры:
        - request: Запрос с данными пользователя (email, пароль и др.)

        Возвращает:
        - Response с данными пользователя и сообщением об успехе или ошибки валидации
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Отправляем письмо с подтверждением регистрации
        self._send_confirmation_email(user)

        return Response({
            "user": serializer.data,
            "message": "Пользователь успешно зарегистрирован. Проверьте вашу почту для подтверждения.",
        }, status=status.HTTP_201_CREATED)

    def _send_confirmation_email(self, user):
        """
        Внутренний метод для отправки email с подтверждением регистрации.

        Параметры:
        - user: Объект пользователя, который зарегистрировался
        """
        subject = 'Подтверждение регистрации'
        confirmation_url = f"{settings.FRONTEND_URL}/confirm-email/{user.id}/"

        html_message = render_to_string('email/registration_confirmation.html', {
            'user': user,
            'confirmation_link': confirmation_url
        })

        plain_message = strip_tags(html_message)

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Класс для просмотра и редактирования профиля пользователя.
    Доступен только аутентифицированным пользователям.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Возвращает объект текущего пользователя"""
        return self.request.user


class ShopView(ListAPIView):
    """
    Класс для получения списка всех магазинов.
    Доступен без аутентификации.
    """
    queryset = Shop.objects.filter(state=True)  # Только активные магазины
    serializer_class = ShopSerializer


class CategoryView(ListAPIView):
    """
    Класс для получения списка всех категорий товаров.
    Доступен без аутентификации.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductInfoView(generics.ListAPIView):
    """
    Класс для получения информации о товарах с возможностью фильтрации.
    Поддерживает фильтрацию по магазину и/или категории.
    """
    serializer_class = ProductInfoSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Возвращает queryset товаров с возможностью фильтрации.

        Доступные параметры запроса:
        - shop_id: ID магазина для фильтрации
        - category_id: ID категории для фильтрации
        """
        queryset = ProductInfo.objects.select_related(
            'shop', 'product'
        ).prefetch_related(
            'product_parameters__parameter'
        ).filter(shop__state=True)  # Только товары из активных магазинов

        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)

        return queryset


class BasketView(generics.GenericAPIView):
    """
    Класс для работы с корзиной пользователя.
    Позволяет просматривать, добавлять и изменять содержимое корзины.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Возвращает queryset для корзины текущего пользователя"""
        return Order.objects.filter(
            user=self.request.user,
            status='basket'
        ).prefetch_related(
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price')))

    def get_basket(self):
        """
        Получает или создает корзину для текущего пользователя.

        Возвращает:
        - Объект корзины (Order) с аннотацией общей суммы
        """
        basket, created = Order.objects.get_or_create(
            user=self.request.user,
            status='basket',
            defaults={'dt': timezone.now()}
        )
        return basket

    def get(self, request, *args, **kwargs):
        """
        Получает содержимое корзины пользователя.

        Возвращает:
        - Данные корзины со списком товаров и общей суммой
        """
        basket = self.get_basket()
        serializer = self.get_serializer(basket)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Добавляет товар в корзину или увеличивает его количество.

        Параметры запроса:
        - product_info_id: ID информации о товаре
        - quantity: Количество товара для добавления

        Возвращает:
        - Обновленные данные корзины или сообщение об ошибке
        """
        basket = self.get_basket()
        serializer = OrderItemSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            # Проверяем наличие товара и достаточное количество на складе
            product_info = ProductInfo.objects.select_related('product', 'shop').get(
                id=serializer.validated_data['product_info_id'],
                shop__state=True,  # Только из активных магазинов
                quantity__gte=serializer.validated_data['quantity']
            )
        except ProductInfo.DoesNotExist:
            return Response(
                {"status": False, "error": "Товар не найден или недостаточно на складе"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Добавляем товар в корзину или обновляем количество
        order_item, created = OrderItem.objects.get_or_create(
            order=basket,
            product_info=product_info,
            defaults={'quantity': serializer.validated_data['quantity']}
        )

        if not created:
            new_quantity = order_item.quantity + serializer.validated_data['quantity']
            if new_quantity > product_info.quantity:
                return Response(
                    {"status": False, "error": "Недостаточно товара на складе"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order_item.quantity = new_quantity
            order_item.save()

        basket.refresh_from_db()
        serializer = self.get_serializer(basket)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BasketItemView(generics.GenericAPIView):
    """
    Класс для работы с отдельными позициями в корзине.
    Позволяет изменять количество или удалять позиции.
    """
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Возвращает queryset позиций в корзине текущего пользователя"""
        return OrderItem.objects.filter(
            order__user=self.request.user,
            order__status='basket'
        ).select_related('product_info__product', 'product_info__shop')

    def get_object(self):
        """Получает конкретную позицию в корзине по ID"""
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, id=self.kwargs['id'])
        return obj

    def put(self, request, *args, **kwargs):
        """
        Изменяет количество товара в позиции корзины.

        Параметры запроса:
        - quantity: Новое количество товара

        Возвращает:
        - Обновленные данные позиции или сообщение об ошибке
        """
        order_item = self.get_object()
        product_info = order_item.product_info

        serializer = self.get_serializer(
            order_item,
            data=request.data,
            partial=True,
            context={'product_info': product_info}
        )
        serializer.is_valid(raise_exception=True)

        new_quantity = serializer.validated_data.get('quantity', order_item.quantity)
        if new_quantity > product_info.quantity:
            return Response(
                {"status": False, "error": f"Доступно только {product_info.quantity} шт."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        """
        Удаляет позицию из корзины.

        Возвращает:
        - Сообщение об успешном удалении
        """
        order_item = self.get_object()
        order_item.delete()
        return Response(
            {"status": True, "message": "Позиция удалена из корзины"},
            status=status.HTTP_204_NO_CONTENT
        )


class ContactView(APIView):
    """
    API для работы с контактами пользователя.
    Поддерживает создание контактов.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ContactSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ContactDetailView(RetrieveUpdateDestroyAPIView):
    """
    API для работы с конкретными контактами пользователя.
    Поддерживает просмотр, обновление, удаление контактов.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()
class ConfirmOrderView(APIView):
    """
    Класс для подтверждения заказа.
    Меняет статус заказа из "корзина" в "подтвержден",
    отправляет email с подтверждением заказа.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Подтверждает заказ из корзины.

        Параметры запроса:
        - basket_id: ID корзины (заказа)
        - contact_id: ID контакта (адреса доставки)

        Возвращает:
        - Подтвержденный заказ или сообщение об ошибке
        """
        basket_id = request.data.get('basket_id')
        contact_id = request.data.get('contact_id')

        # Проверка обязательных параметров
        if not basket_id or not contact_id:
            return Response(
                {"status": False, "error": "Необходимо указать basket_id и contact_id."},
                status=400
            )

        try:
            # Получаем корзину пользователя
            basket = Order.objects.get(id=basket_id, user=request.user, status='basket')
        except Order.DoesNotExist:
            return Response(
                {"status": False, "error": "Корзина не найдена или не принадлежит пользователю."},
                status=404
            )

        # Проверяем, что корзина не пуста
        if not basket.ordered_items.exists():
            return Response(
                {"status": False, "error": "Невозможно подтвердить пустой заказ."},
                status=400
            )

        try:
            # Проверяем контакт пользователя
            contact = Contact.objects.get(id=contact_id, user=request.user)
        except Contact.DoesNotExist:
            return Response(
                {"status": False, "error": "Контакт не найден или не принадлежит пользователю."},
                status=404
            )

        # Подтверждаем заказ
        basket.status = 'confirmed'
        basket.contact = contact
        basket.dt = timezone.now()
        basket.save()

        # Отправляем email с подтверждением заказа
        self._send_order_confirmation_email(request.user, basket)

        return Response(
            {
                "status": True,
                "message": "Заказ успешно подтвержден.",
                "order_id": basket.id,
                "total_sum": basket.total_sum
            },
            status=200
        )

    def _send_order_confirmation_email(self, user, order):
        """
        Внутренний метод для отправки email с подтверждением заказа.

        Параметры:
        - user: Объект пользователя
        - order: Объект подтвержденного заказа
        """
        subject = 'Подтверждение вашего заказа'
        html_message = render_to_string('email/order_confirmation.html', {
            'user': user,
            'order': order,
            'order_items': order.ordered_items.all(),
            'order_link': f"{settings.FRONTEND_URL}/orders/{order.id}/"
        })
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to = user.email

        send_mail(
            subject,
            plain_message,
            from_email,
            [to],
            html_message=html_message,
            fail_silently=False,
        )


class ListOrdersView(APIView):
    """
    Класс для получения списка заказов пользователя.
    Не включает заказы со статусом "корзина".
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получает список всех заказов пользователя, кроме корзин.

        Возвращает:
        - Список заказов с детализацией позиций
        """
        orders = Order.objects.filter(
            user=request.user
        ).exclude(
            status='basket'  # Исключаем корзины
        ).order_by('-dt').prefetch_related(
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product__category'
        )

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class ConfirmEmailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_email_confirmed = True
            user.save()
            return Response(
                {"status": "success", "message": "Email успешно подтверждён!"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )