import os
import sys

import json

import requests

from utilities import set_main_folder, config_value

# Пути к папке скрипта
script_path = os.path.dirname(os.path.abspath(__file__))

# Устанавливаем основную папку проекта
set_main_folder(script_path)

# Адрес и порт веб-сервиса
url = 'http://localhost'
port = config_value(None, 'MAIN', 'port', None)
if port is None:
    raise ValueError("Порт не задан")

# Запрос описания задачи
prompt = input(f'''Будет выполнен запрос к веб-сервису {url}:{port}.
Необходимо ввести описание задачи.
Пример: Продажи за неделю с отбором по контрагенту.

Опишите задачу: ''')
print('Ожидайте ответа...')

# Получения и вывод ответа
headers = {'Content-Type': 'application/json; charset=utf-8'}
response = requests.post(f'{url}:{port}', json={'prompt': prompt}, headers=headers)

print('\nСтатус ответа:', response.status_code)
print('Ответ:\n', json.loads(response.text)['response'])