from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'company')

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'state')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')

@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'name', 'quantity', 'price', 'price_rrc')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )

@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('product_info', 'parameter', 'value')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'dt', 'status')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_info', 'quantity')


