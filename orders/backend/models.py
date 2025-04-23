from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('buyer', 'Покупатель'),
        ('supplier', 'Поставщик'),
    )

    # Указываем уникальные related_name для групп и разрешений
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",  # Уникальное имя
        related_query_name="user"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",  # Уникальное имя
        related_query_name="user"
    )
    username = models.CharField(max_length=30, unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='buyer')
    company = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
class Shop(models.Model):
    name = models.CharField(max_length=50)
    url = models.URLField(null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    state = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'

class Category(models.Model):
    name = models.CharField(max_length=40)
    shops = models.ManyToManyField(Shop, related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Product(models.Model):
    name = models.CharField(max_length=80)
    model = models.CharField(max_length=100, blank=True, default='')
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

class ProductInfo(models.Model):
    product = models.ForeignKey(Product, related_name='product_infos', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, related_name='product_infos', on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    price_rrc = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информация о продуктах'

class Parameter(models.Model):
    name = models.CharField(max_length=40)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'

class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, related_name='product_parameters', on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, related_name='product_parameters', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Параметр продукта'
        verbose_name_plural = 'Параметры продуктов'


class Order(models.Model):
    STATUS_CHOICES = (
        ('basket', 'Статус корзины'),
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('assembled', 'Собран'),
        ('sent', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    )

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='ordered_items', on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, related_name='ordered_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'


class Contact(models.Model):
    TYPE_CHOICES = (
        ('phone', 'Телефон'),
        ('address', 'Адрес'),
    )

    user = models.ForeignKey(User, related_name='contacts', on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    value = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'