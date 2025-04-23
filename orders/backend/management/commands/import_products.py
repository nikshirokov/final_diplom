import yaml
from django.core.management.base import BaseCommand
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter


class Command(BaseCommand):
    help = 'Импорт товаров из YAML файла'

    def handle(self, *args, **options):
        with open('shop1.yaml', 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

            # Создаем или получаем магазин
            shop, _ = Shop.objects.get_or_create(
                name=data['shop'],
                defaults={'url': None, 'state': True}
            )

            # Обрабатываем категории
            for category_data in data['categories']:
                category, _ = Category.objects.get_or_create(
                    id=category_data['id'],
                    defaults={'name': category_data['name']}
                )
                category.shops.add(shop)

            # Обрабатываем товары
            for product_data in data['goods']:
                # Получаем категорию
                try:
                    category = Category.objects.get(id=product_data['category'])
                except Category.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f"Категория с id {product_data['category']} не найдена. Пропускаем товар {product_data['name']}"
                    ))
                    continue

                # Создаем или обновляем продукт
                product, _ = Product.objects.get_or_create(
                    name=product_data['name'],
                    category=category,
                    defaults={'model': product_data.get('model', '')}
                )

                # Создаем или обновляем информацию о продукте
                product_info, created = ProductInfo.objects.update_or_create(
                    product=product,
                    shop=shop,
                    defaults={
                        'name': product_data['name'],
                        'quantity': product_data['quantity'],
                        'price': product_data['price'],
                        'price_rrc': product_data['price_rrc']
                    }
                )

                # Обрабатываем параметры
                for param_name, param_value in product_data['parameters'].items():
                    # Создаем или получаем параметр
                    parameter, _ = Parameter.objects.get_or_create(name=param_name)

                    # Создаем связь параметра с продуктом
                    ProductParameter.objects.update_or_create(
                        product_info=product_info,
                        parameter=parameter,
                        defaults={'value': str(param_value)}
                    )

        self.stdout.write(self.style.SUCCESS('Импорт успешно завершен!'))