# Дипломный проект профессии «Python-разработчик: расширенный курс»

## Backend-приложение для автоматизации закупок

### Общее описание приложения

Приложение предназначено для автоматизации закупок в розничной сети через REST API.

## 📌 Основные возможности

- ✅ Регистрация и авторизация пользователей
- 🔍 Поиск и фильтрация товаров
- 🛒 Корзина с возможностью оформления заказа
- 📦 Личный кабинет с историей заказов
- ⚙️ Админ-панель для управления контентом

## 🛠 Технологический стек

**Backend:**
- Python 3.10+
- Django 4.2
- Django REST Framework

## 🚀 Установка и запуск

1. Клонируйте репозиторий:
```
git clone https://github.com/nikshirokov/final_diplom.git
cd final_diplom
```
Создайте и активируйте виртуальное окружение:
```
python -m venv venv
# Для Windows:
venv\Scripts\activate
# Для Linux/MacOS:
source venv/bin/activate
```

2. Установите зависимости:
```
pip install -r requirements.txt
```
3. Запустить БД:
```
docker compose up -d
```
4. Применить миграции:
```
python manage.py migrate
```

5. Создать суперпользователя:
```
python manage.py createsuperuser
```

6.  Запустите сервер:
```
python manage.py runserver
```
### Применение импорта продуктов для примера
```
python manage.py import_products
```


