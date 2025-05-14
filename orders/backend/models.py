from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class User(AbstractUser):
    """
    Модель пользователя с расширенными полями.
    Включает функционал для подтверждения email и разграничения типов пользователей.
    """

    class UserType(models.TextChoices):
        """Типы пользователей системы"""
        BUYER = 'buyer', _('Покупатель')
        SUPPLIER = 'supplier', _('Поставщик')

    # Переопределение стандартных полей для избежания конфликтов
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

    # Основные поля
    username = models.CharField(
        _('username'),
        max_length=30,
        unique=True,
        db_index=True,
        help_text=_('Уникальное имя пользователя')
    )
    email = models.EmailField(
        _('email address'),
        unique=True,
        blank=False,
        help_text=_('Электронная почта (должна быть уникальной)')
    )
    user_type = models.CharField(
        _('user type'),
        max_length=10,
        choices=UserType.choices,
        default=UserType.BUYER,
        db_index=True,
        help_text=_('Тип пользователя в системе')
    )
    company = models.CharField(
        _('company'),
        max_length=100,
        blank=True,
        help_text=_('Название компании (для поставщиков)')
    )
    position = models.CharField(
        _('position'),
        max_length=100,
        blank=True,
        help_text=_('Должность в компании')
    )

    # Поля для подтверждения email
    is_email_confirmed = models.BooleanField(
        _('email confirmed'),
        default=False,
        db_index=True,
        help_text=_('Подтвержден ли email пользователя')
    )
    email_confirmation_token = models.CharField(
        _('email confirmation token'),
        max_length=64,
        blank=True,
        null=True,
        help_text=_('Токен для подтверждения email')
    )
    email_confirmation_sent = models.DateTimeField(
        _('confirmation email sent at'),
        blank=True,
        null=True,
        help_text=_('Когда было отправлено письмо с подтверждением')
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['username']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_email_confirmed']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def clean(self):
        """Валидация модели перед сохранением"""
        if self.user_type == self.UserType.SUPPLIER and not self.company:
            raise ValidationError(_('Для поставщика необходимо указать компанию'))
        super().clean()


class Shop(models.Model):
    """
    Модель магазина/продавца.
    Содержит информацию о магазинах, доступных в системе.
    """

    name = models.CharField(
        _('name'),
        max_length=50,
        db_index=True,
        help_text=_('Название магазина')
    )
    url = models.URLField(
        _('url'),
        null=True,
        blank=True,
        validators=[URLValidator()],
        help_text=_('URL сайта магазина')
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shop',
        help_text=_('Пользователь-владелец магазина')
    )
    state = models.BooleanField(
        _('state'),
        default=True,
        db_index=True,
        help_text=_('Флаг активности магазина')
    )
    delivery_options = models.JSONField(
        _('delivery options'),
        default=dict,
        blank=True,
        help_text=_('Доступные способы доставки и их стоимость')
    )

    class Meta:
        verbose_name = _('Магазин')
        verbose_name_plural = _('Магазины')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_shop_name'
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Проверка, что магазин с таким именем уже не существует"""
        if Shop.objects.exclude(pk=self.pk).filter(name=self.name).exists():
            raise ValidationError(_('Магазин с таким названием уже существует'))
        super().clean()


class Category(models.Model):
    """
    Модель категорий товаров.
    Товары могут принадлежать к разным категориям.
    """

    name = models.CharField(
        _('name'),
        max_length=40,
        db_index=True,
        help_text=_('Название категории')
    )
    shops = models.ManyToManyField(
        Shop,
        related_name='categories',
        blank=True,
        verbose_name=_('shops'),
        help_text=_('Магазины, в которых представлена эта категория')
    )

    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_category_name'
            )
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Модель продукта/товара.
    Описывает основные характеристики товара без привязки к магазину.
    """

    name = models.CharField(
        _('name'),
        max_length=80,
        db_index=True,
        help_text=_('Наименование товара')
    )
    model = models.CharField(
        _('model'),
        max_length=100,
        blank=True,
        default='',
        help_text=_('Модель/артикул товара')
    )
    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name=_('category'),
        help_text=_('Категория товара')
    )

    class Meta:
        verbose_name = _('Продукт')
        verbose_name_plural = _('Продукты')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'model']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.model})" if self.model else self.name


class Parameter(models.Model):
    """
    Модель параметров товара.
    Описывает возможные характеристики товаров (цвет, размер, вес и т.д.).
    """

    name = models.CharField(
        _('name'),
        max_length=40,
        db_index=True,
        help_text=_('Название параметра')
    )

    class Meta:
        verbose_name = _('Параметр')
        verbose_name_plural = _('Параметры')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_parameter_name'
            )
        ]

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """
    Модель информации о продукте в конкретном магазине.
    Содержит специфичные для магазина данные: цену, количество и т.д.
    """

    product = models.ForeignKey(
        Product,
        related_name='product_infos',
        on_delete=models.CASCADE,
        verbose_name=_('product'),
        help_text=_('Базовый продукт')
    )
    shop = models.ForeignKey(
        Shop,
        related_name='product_infos',
        on_delete=models.CASCADE,
        verbose_name=_('shop'),
        help_text=_('Магазин, в котором представлен товар')
    )
    name = models.CharField(
        _('name'),
        max_length=80,
        help_text=_('Название товара в магазине (может отличаться от базового)')
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(0)],
        help_text=_('Доступное количество товара')
    )
    price = models.DecimalField(
        _('price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Цена товара')
    )
    price_rrc = models.DecimalField(
        _('recommended retail price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Рекомендуемая розничная цена')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        db_index=True,
        help_text=_('Доступен ли товар для заказа')
    )

    class Meta:
        verbose_name = _('Информация о продукте')
        verbose_name_plural = _('Информация о продуктах')
        unique_together = ('product', 'shop')
        ordering = ['product', 'shop']
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name='quantity_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(price__gt=0),
                name='price_positive'
            )
        ]

    def __str__(self):
        return f"{self.product} в {self.shop}"

    def check_quantity(self, quantity):
        """
        Проверяет, доступно ли указанное количество товара.

        Аргументы:
            quantity (int): Запрашиваемое количество

        Возвращает:
            bool: True если товар активен и доступен в нужном количестве
        """
        return self.is_active and self.quantity >= quantity


class ProductParameter(models.Model):
    """
    Модель связи параметра с продуктом.
    Хранит конкретные значения параметров для товара в магазине.
    """

    product_info = models.ForeignKey(
        ProductInfo,
        related_name='product_parameters',
        on_delete=models.CASCADE,
        verbose_name=_('product info'),
        help_text=_('Информация о продукте')
    )
    parameter = models.ForeignKey(
        Parameter,
        related_name='product_parameters',
        on_delete=models.CASCADE,
        verbose_name=_('parameter'),
        help_text=_('Параметр товара')
    )
    value = models.CharField(
        _('value'),
        max_length=100,
        help_text=_('Значение параметра')
    )

    class Meta:
        verbose_name = _('Параметр продукта')
        verbose_name_plural = _('Параметры продуктов')
        unique_together = ('product_info', 'parameter')
        ordering = ['parameter']

    def __str__(self):
        return f"{self.parameter}: {self.value}"


class Order(models.Model):
    """
    Модель заказа.
    Содержит информацию о заказах пользователей и их статусах.
    """

    class Status(models.TextChoices):
        """Статусы заказа"""
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
        db_index=True,
        help_text=_('Пользователь, сделавший заказ')
    )
    dt = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        db_index=True,
        help_text=_('Дата и время создания заказа')
    )
    updated = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        db_index=True,
        help_text=_('Дата и время последнего обновления')
    )
    status = models.CharField(
        _('status'),
        max_length=15,
        choices=Status.choices,
        default=Status.BASKET,
        db_index=True,
        help_text=_('Текущий статус заказа')
    )
    contact = models.ForeignKey(
        'Contact',
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('contact'),
        help_text=_('Контактные данные для доставки')
    )
    delivery_notes = models.TextField(
        _('delivery notes'),
        blank=True,
        help_text=_('Дополнительные заметки по доставке')
    )

    class Meta:
        verbose_name = _('Заказ')
        verbose_name_plural = _('Заказы')
        ordering = ['-dt']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status='basket') | models.Q(contact__isnull=False),
                name='contact_required_for_non_basket_orders'
            )
        ]

    def __str__(self):
        return f"Заказ #{self.id} - {self.get_status_display()}"

    @property
    def total_sum(self):
        """Вычисляет общую сумму заказа"""
        return sum(
            item.quantity * item.product_info.price
            for item in self.ordered_items.all()
        )

    def clean(self):
        """Валидация заказа перед сохранением"""
        if self.status != self.Status.BASKET and not self.contact:
            raise ValidationError(_('Для подтвержденных заказов необходим контакт'))
        super().clean()

    def confirm(self, contact):
        """
        Подтверждает заказ (переводит из корзины в новый заказ).

        Аргументы:
            contact (Contact): Контактные данные для доставки

        Исключения:
            ValueError: Если заказ уже подтвержден или пуст
        """
        if self.status != self.Status.BASKET:
            raise ValueError(_('Можно подтверждать только заказы в статусе корзины'))
        if not contact:
            raise ValueError(_('Необходимо указать контактные данные'))
        if not self.ordered_items.exists():
            raise ValueError(_('Нельзя подтвердить пустой заказ'))

        self.status = self.Status.NEW
        self.contact = contact
        self.save()


class OrderItem(models.Model):
    """
    Модель позиции в заказе.
    Связывает заказ с конкретным товаром и его количеством.
    """

    order = models.ForeignKey(
        Order,
        related_name='ordered_items',
        on_delete=models.CASCADE,
        verbose_name=_('order'),
        help_text=_('Заказ, к которому относится позиция')
    )
    product_info = models.ForeignKey(
        ProductInfo,
        related_name='ordered_items',
        on_delete=models.CASCADE,
        verbose_name=_('product info'),
        help_text=_('Информация о заказанном товаре')
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(1)],
        help_text=_('Количество товара')
    )

    class Meta:
        verbose_name = _('Позиция заказа')
        verbose_name_plural = _('Позиции заказа')
        unique_together = ('order', 'product_info')
        ordering = ['order', 'product_info']
        indexes = [
            models.Index(fields=['order', 'product_info']),
            models.Index(fields=['product_info']),
        ]

    def __str__(self):
        return f"{self.product_info} x {self.quantity}"

    @property
    def item_sum(self):
        """Вычисляет сумму по позиции заказа"""
        return self.quantity * self.product_info.price

    def clean(self):
        """Проверяет доступность товара перед сохранением"""
        if not self.product_info.check_quantity(self.quantity):
            raise ValidationError(_('Недостаточно товара на складе'))
        super().clean()


# models.py
class Contact(models.Model):
    """
    Модель контактных данных пользователя.
    Используется для хранения адресов доставки и контактных телефонов.
    """

    class ContactType(models.TextChoices):
        """Типы контактных данных"""
        PHONE = 'phone', _('Телефон')
        ADDRESS = 'address', _('Адрес')

    user = models.ForeignKey(
        User,
        related_name='contacts',
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь')
    )
    type = models.CharField(
        _('Тип'),
        max_length=10,
        choices=ContactType.choices,
        db_index=True
    )

    # Поля для адреса
    city = models.CharField(_('Город'), max_length=50, blank=True, null=True)
    street = models.CharField(_('Улица'), max_length=100, blank=True, null=True)
    house = models.CharField(_('Дом'), max_length=15, blank=True, null=True)
    apartment = models.CharField(_('Квартира'), max_length=15, blank=True, null=True)
    postal_code = models.CharField(_('Индекс'), max_length=20, blank=True, null=True)

    # Поле для телефона
    phone = models.CharField(_('Телефон'), max_length=20, blank=True, null=True)

    # Общее поле (автозаполняемое)
    value = models.CharField(
        _('Форматированное значение'),
        max_length=200,
        blank=True,
        editable=False  # Поле только для чтения в админке
    )

    class Meta:
        verbose_name = _('Контакт')
        verbose_name_plural = _('Контакты')
        ordering = ['user', 'type']

    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"

    def save(self, *args, **kwargs):
        """Автоматически заполняет поле value перед сохранением"""
        self.full_clean()  # Вызываем валидацию
        self._update_value_field()
        super().save(*args, **kwargs)

    def _update_value_field(self):
        """Обновляет поле value на основе других полей"""
        if self.type == self.ContactType.ADDRESS:
            address_parts = filter(None, [
                self.city,
                self.street,
                f"д.{self.house}" if self.house else None,
                f"кв.{self.apartment}" if self.apartment else None
            ])
            self.value = ", ".join(address_parts)
        elif self.type == self.ContactType.PHONE:
            self.value = self.phone or ""

    def clean(self):
        """Валидация модели"""
        if self.type == self.ContactType.ADDRESS:
            if not all([self.city, self.street, self.house]):
                raise ValidationError(_('Для адреса необходимо указать город, улицу и дом'))
        elif self.type == self.ContactType.PHONE and not self.phone:
            raise ValidationError(_('Для телефона необходимо указать номер'))