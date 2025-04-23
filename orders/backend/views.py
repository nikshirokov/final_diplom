from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Shop, Category, ProductInfo, Order, OrderItem
from .serializers import ShopSerializer, CategorySerializer, UserRegisterSerializer, UserProfileSerializer, \
    ProductInfoSerializer, MyTokenObtainPairSerializer, OrderSerializer, OrderItemSerializer
from django.utils import timezone

# Create your views here.
class LoginAccountView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterAccountView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": serializer.data,
            "message": "User created successfully",
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ShopView(ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class CategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductInfoView(generics.ListAPIView):
    serializer_class = ProductInfoSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = ProductInfo.objects.select_related(
            'shop', 'product'
        ).prefetch_related(
            'product_parameters__parameter'
        )

        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)

        return queryset


class BasketView(generics.GenericAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user,
            status='basket'
        ).prefetch_related(
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter'
        ).annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))
        ).distinct()

    def get_basket(self):
        """Получает или создает корзину с аннотацией общей суммы"""
        basket, created = Order.objects.get_or_create(
            user=self.request.user,
            status='basket',
            defaults={'dt': timezone.now()}
        )
        return basket

    def get(self, request, *args, **kwargs):
        basket = self.get_basket()
        serializer = self.get_serializer(basket)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        basket = self.get_basket()
        serializer = OrderItemSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            product_info = ProductInfo.objects.select_related('product', 'shop').get(
                id=serializer.validated_data['product_info_id'],
                quantity__gte=serializer.validated_data['quantity']  # Проверка наличия
            )
        except ProductInfo.DoesNotExist:
            return Response(
                {"status": False, "error": "Товар не найден или недостаточно на складе"},
                status=status.HTTP_404_NOT_FOUND
            )

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

        # Обновляем аннотации
        basket.refresh_from_db()
        serializer = self.get_serializer(basket)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BasketItemView(generics.GenericAPIView):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(
            order__user=self.request.user,
            order__status='basket'
        ).select_related('product_info__product', 'product_info__shop')

    def get_object(self):
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, id=self.kwargs['id'])
        return obj

    def put(self, request, *args, **kwargs):
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
        order_item = self.get_object()
        order_item.delete()
        return Response(
            {"status": True, "message": "Позиция удалена из корзины"},
            status=status.HTTP_204_NO_CONTENT
        )