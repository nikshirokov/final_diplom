from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, URLValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Модель пользователя с расширенными полями"""

    class UserType(models.TextChoices):
        BUYER = 'buyer', _('Покупатель')
        SUPPLIER = 'supplier', _('Поставщик')

    # Указываем уникальные related_name для групп и разрешений
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="custom_user_set",
        related_query_name="user"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="user"
    )

    username = models.CharField(
        _('username'),
        max_length=30,
        unique=True,
        db_index=True
    )
    email = models.EmailField(
        _('email address'),
        unique=True,
        blank=False
    )
    user_type = models.CharField(
        _('user type'),
        max_length=10,
        choices=UserType.choices,
        default=UserType.BUYER,
        db_index=True
    )
    company = models.CharField(
        _('company'),
        max_length=100,
        blank=True
    )
    position = models.CharField(
        _('position'),
        max_length=100,
        blank=True
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Shop(models.Model):
    """Модель магазина"""

    name = models.CharField(
        _('name'),
        max_length=50,
        db_index=True
    )
    url = models.URLField(
        _('url'),
        null=True,
        blank=True,
        validators=[URLValidator()]
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shop'
    )
    state = models.BooleanField(
        _('state'),
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = _('Магазин')
        verbose_name_plural = _('Магазины')
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Модель категории товаров"""

    name = models.CharField(
        _('name'),
        max_length=40,
        db_index=True
    )
    shops = models.ManyToManyField(
        Shop,
        related_name='categories',
        blank=True,
        verbose_name=_('shops')
    )

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель продукта"""

    name = models.CharField(
        _('name'),
        max_length=80,
        db_index=True
    )
    model = models.CharField(
        _('model'),
        max_length=100,
        blank=True,
        default=''
    )
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name=_('category')
    )

    class Meta:
        verbose_name = _('Продукт')
        verbose_name_plural = _('Продукты')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.model})" if self.model else self.name


class Parameter(models.Model):
    """Модель параметра товара"""

    name = models.CharField(
        _('name'),
        max_length=40,
        db_index=True
    )

    class Meta:
        verbose_name = _('Параметр')
        verbose_name_plural = _('Параметры')
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """Модель информации о продукте в магазине"""

    product = models.ForeignKey(
        Product,
        related_name='product_infos',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    shop = models.ForeignKey(
        Shop,
        related_name='product_infos',
        on_delete=models.CASCADE,
        verbose_name=_('shop')
    )
    name = models.CharField(
        _('name'),
        max_length=80
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(0)]
    )
    price = models.DecimalField(
        _('price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    price_rrc = models.DecimalField(
        _('recommended retail price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    class Meta:
        verbose_name = _('Информация о продукте')
        verbose_name_plural = _('Информация о продуктах')
        unique_together = ('product', 'shop')
        ordering = ['product', 'shop']

    def __str__(self):
        return f"{self.product} в {self.shop}"


class ProductParameter(models.Model):
    """Модель связи параметра с продуктом"""

    product_info = models.ForeignKey(
        ProductInfo,
        related_name='product_parameters',
        on_delete=models.CASCADE,
        verbose_name=_('product info')
    )
    parameter = models.ForeignKey(
        Parameter,
        related_name='product_parameters',
        on_delete=models.CASCADE,
        verbose_name=_('parameter')
    )
    value = models.CharField(
        _('value'),
        max_length=100
    )

    class Meta:
        verbose_name = _('Параметр продукта')
        verbose_name_plural = _('Параметры продуктов')
        unique_together = ('product_info', 'parameter')
        ordering = ['parameter']

    def __str__(self):
        return f"{self.parameter}: {self.value}"


class Order(models.Model):
    """Модель заказа"""

    class Status(models.TextChoices):
        BASKET = 'basket', _('Статус корзины')
        NEW = 'new', _('Новый')
        CONFIRMED = 'confirmed', _('Подтвержден')
        ASSEMBLED = 'assembled', _('Собран')
        SENT = 'sent', _('Отправлен')
        DELIVERED = 'delivered', _('Доставлен')
        CANCELED = 'canceled', _('Отменен')

    user = models.ForeignKey(
        User,
        related_name='orders',
        on_delete=models.CASCADE,
        verbose_name=_('user'),
        db_index=True
    )
    dt = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        db_index=True
    )
    updated = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        db_index=True
    )
    status = models.CharField(
        _('status'),
        max_length=15,
        choices=Status.choices,
        default=Status.BASKET,
        db_index=True
    )

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-dt']

    def __str__(self):
        return f"Заказ #{self.id} - {self.get_status_display()}"

    @property
    def total_sum(self):
        """Общая сумма заказа"""
        return sum(
            item.quantity * item.product_info.price
            for item in self.ordered_items.all()
        )


class OrderItem(models.Model):
    """Модель позиции заказа"""

    order = models.ForeignKey(
        Order,
        related_name='ordered_items',
        on_delete=models.CASCADE,
        verbose_name=_('order')
    )
    product_info = models.ForeignKey(
        ProductInfo,
        related_name='ordered_items',
        on_delete=models.CASCADE,
        verbose_name=_('product info')
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = _('Позиция заказа')
        verbose_name_plural = _('Позиции заказа')
        unique_together = ('order', 'product_info')
        ordering = ['order', 'product_info']

    def __str__(self):
        return f"{self.product_info} x {self.quantity}"

    @property
    def item_sum(self):
        """Сумма по позиции"""
        return self.quantity * self.product_info.price


class Contact(models.Model):
    """Модель контактов пользователя"""

    class ContactType(models.TextChoices):
        PHONE = 'phone', _('Телефон')
        ADDRESS = 'address', _('Адрес')

    user = models.ForeignKey(
        User,
        related_name='contacts',
        on_delete=models.CASCADE,
        verbose_name=_('user')
    )
    type = models.CharField(
        _('type'),
        max_length=10,
        choices=ContactType.choices,
        db_index=True
    )
    value = models.CharField(
        _('value'),
        max_length=100
    )

    class Meta:
        verbose_name = _('Контакт')
        verbose_name_plural = _('Контакты')
        ordering = ['user', 'type']

    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"