import json

import requests

import os

from utilities import set_main_folder, config_value

# Путь к папке файлов AI-асистента
if getattr(sys, 'frozen', False):
    # Если приложение упаковано cx_Freeze
    project_path = os.path.dirname(sys.executable)
else:
    # Если запускается как обычный скрипт
    project_path = os.path.dirname(os.path.abspath(__file__))

# Устанавливаем путь для использования во всех модулях
set_main_folder(project_path)

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