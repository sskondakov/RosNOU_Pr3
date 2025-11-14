import os
import sys

# Пути к папкам скрипта и сторонних библиотек
script_path = os.path.dirname(os.path.abspath(__file__))
packages_path = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages')

# Устанавливаем папки для импорта модулей
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)
if script_path not in sys.path:
    sys.path.insert(0, script_path)

import json

import requests

from utilities import set_main_folder, config_value

# Устанавливаем основную папку проекта
set_main_folder(script_path)

# Адрес и порт веб-сервиса
url = 'http://localhost'
port = config_value(None, 'MAIN', 'port', None)
if port is None:
    raise ValueError("Порт не задан")

# Запрос описания задачи
prompt = input('''Будет выполнен запрос к веб-сервису {url}:{port}.
Необходимо ввести описание задачи.
Пример: Продажи за неделю с отбором по контрагенту.

Опишите задачу: ''')
print('Ожидайте ответа...')

# Получения и вывод ответа
headers = {'Content-Type': 'application/json; charset=utf-8'}
response = requests.post(f'{url}:{port}', json={'prompt': prompt}, headers=headers)

print('\nСтатус ответа:', response.status_code)
print('Ответ:\n', json.loads(response.text)['response'])