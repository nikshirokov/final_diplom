from django.contrib import admin
from django.utils.html import format_html
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'company', 'position', 'is_active')
    list_filter = ('user_type', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'company')
    list_editable = ('is_active',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Work info', {'fields': ('company', 'position', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'groups')}),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_url', 'state', 'user')
    list_filter = ('state',)
    search_fields = ('name', 'user__username')
    raw_id_fields = ('user',)

    def display_url(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url) if obj.url else '-'

    display_url.short_description = 'URL'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'model')
    raw_id_fields = ('category',)


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'quantity', 'display_price', 'display_rrc')
    list_filter = ('shop',)
    search_fields = ('product__name', 'shop__name')
    raw_id_fields = ('product', 'shop')

    def display_price(self, obj):
        return f"{obj.price:,.2f} ₽"

    display_price.short_description = 'Цена'

    def display_rrc(self, obj):
        return f"{obj.price_rrc:,.2f} ₽"

    display_rrc.short_description = 'РРЦ'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_shops')
    search_fields = ('name',)

    def display_shops(self, obj):
        return ", ".join([shop.name for shop in obj.shops.all()])

    display_shops.short_description = 'Магазины'


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_products_count')
    search_fields = ('name',)

    def display_products_count(self, obj):
        return obj.product_parameters.count()

    display_products_count.short_description = 'Товары'


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('product_info', 'parameter', 'value')
    list_filter = ('parameter',)
    search_fields = ('product_info__product__name', 'parameter__name')
    raw_id_fields = ('product_info', 'parameter')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_dt', 'status', 'display_total')
    list_filter = ('status',)
    search_fields = ('user__username', 'id')
    date_hierarchy = 'dt'
    readonly_fields = ('dt', 'updated')

    def display_dt(self, obj):
        return obj.dt.strftime("%d.%m.%Y %H:%M")

    display_dt.short_description = 'Дата'

    def display_total(self, obj):
        return f"{obj.total_sum:,.2f} ₽"

    display_total.short_description = 'Сумма'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_info', 'quantity', 'display_sum')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product_info__product__name')
    raw_id_fields = ('order', 'product_info')

    def display_sum(self, obj):
        return f"{obj.product_info.price * obj.quantity:,.2f} ₽"

    display_sum.short_description = 'Сумма'