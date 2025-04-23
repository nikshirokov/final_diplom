import requests
# '''Регистрация'''
# url = "http://localhost:8000/api/v1/user/register/"
# data = {
#     'username': "hLX0e@example2",
#     "email": "hLX0e@example2.com",
#     "password": "password",
#     "first_name": "John",
#     "last_name": "Doe",
#     "company": "Example Company",
#     "position": "Manager",
#     "user_type": "buyer"
# }
#
# response = requests.post(url, json=data)
#
# print("Статус код:", response.status_code)
# print("Ответ сервера:", response.json())
#
# '''Вход'''
# response = requests.post('http://localhost:8000/api/v1/user/login/', data={
#     'username': 'hLX0e@example2',
#     'password': 'password'
# })
# print("Статус код:", response.status_code)
# print("Ответ сервера:", response.json())
#
# '''Просмотр профиля'''
# access_token = response.json()['access']
# headers = {'Authorization': f'Bearer {access_token}'}
# url = 'http://localhost:8000/api/v1/user/profile/'
# response = requests.get(url, headers=headers)
# print("Информация о пользователе:", response.json())
#
# '''Проверка пустой корзины'''
# basket_url = 'http://localhost:8000/api/v1/basket/'
# response = requests.get(basket_url, headers=headers)
# print("Пустая корзина:", response.json())
#
# '''Добавление товара'''
# add_item_url = 'http://localhost:8000/api/v1/basket/'
# item_data = {'product_info_id': 2, 'quantity': 1}  # ID существующего товара
# response = requests.post(add_item_url, json=item_data, headers=headers)
# print("Добавление товара:", response.json())
#
#
# '''Проверка обновленной корзины'''
# basket_url = 'http://localhost:8000/api/v1/basket/'
# response = requests.get(basket_url, headers=headers)
# print("Корзина с товарами:", response.json())
#
# '''обновление корзины'''
# basket_data = response.json()
# first_item_id = basket_data['ordered_items'][0]['id']
# update_url = f'http://localhost:8000/api/v1/basket/{first_item_id}/'
# update_data = {'quantity': 2}
#
# response = requests.put(update_url, json=update_data, headers=headers)
#
# if response.status_code != 200:
#     print("Ошибка обновления количества:", response.text)
# else:
#     print("Количество обновлено:", response.json())
#
# '''Удаление товара'''
# basket_data = response.json()
# update_url = f'http://localhost:8000/api/v1/basket/{first_item_id}/'
# response = requests.delete(update_url, headers=headers)
#
# if response.status_code != 204:
#     print("Ошибка удаления товара:", response.text)
# else:
#     print("Товар успешно удалён")
#
# '''Финальная проверка корзины'''
# response = requests.get(basket_url, headers=headers)
# print("Финальное состояние корзины:", response.json())


# url = 'http://localhost:8000/api/v1/shops/'
# response = requests.get(url, headers=headers)
# print(response.status_code)
# print(response.json())
#
# url = 'http://localhost:8000/api/v1/categories/'
# response = requests.get(url, headers=headers)
# print(response.status_code)
# print(response.json())








