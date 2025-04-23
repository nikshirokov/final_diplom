from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Category, Shop, ProductInfo, Product, ProductParameter, OrderItem, Order, Contact


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Добавляем кастомные поля в токен
        token['user_type'] = user.user_type
        token['email'] = user.email
        return token

    def validate(self, attrs):
        # Стандартная валидация и получение токенов
        data = super().validate(attrs)

        # Добавляем дополнительные данные в ответ
        refresh = data.pop('refresh', None)  # Убираем refresh из основного ответа
        access = data.pop('access', None)  # Убираем access из основного ответа

        # Формируем новый ответ
        response_data = {
            'access': access,
            'refresh': refresh,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'user_type': self.user.user_type,
                'company': self.user.company,
                'position': self.user.position,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name
            }
        }

        return response_data


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        default='buyer',
        required=False
    )

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'company', 'position',
            'password', 'user_type'  # Добавили user_type
        )
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'company': {'required': False, 'allow_blank': True},
            'position': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        # Извлекаем пароль отдельно
        password = validated_data.pop('password')

        # Создаем пользователя с хешированным паролем
        user = User.objects.create_user(
            password=password,  # Пароль хешируется автоматически в create_user
            **validated_data
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    contacts = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts')
        read_only_fields = ('id',)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'name', 'phone', 'email')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer()
    product_parameters = ProductParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)
    product_info_id = serializers.IntegerField(write_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'product_info_id', 'quantity', 'total_price']
        read_only_fields = ['id', 'total_price']

    def get_total_price(self, obj):
        return obj.product_info.price * obj.quantity

    def validate(self, data):
        product_info_id = data.get('product_info_id')
        quantity = data.get('quantity', 1)

        if 'product_info' in self.context:
            product_info = self.context['product_info']
        else:
            product_info = ProductInfo.objects.filter(id=product_info_id).first()

        if not product_info:
            raise serializers.ValidationError("Товар не найден")

        if quantity > product_info.quantity:
            raise serializers.ValidationError(
                f"Доступно только {product_info.quantity} шт. на складе"
            )

        return data

class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemSerializer(many=True, read_only=True)
    total_sum = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'dt', 'ordered_items', 'total_sum']
        read_only_fields = fields
