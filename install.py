import os

import uuid

import configparser
from zipfile import ZipFile

# Пути к папке скрипта
script_path = os.path.dirname(os.path.abspath(__file__))

###############################################################################
# Установка сторонних пакетов

# Путь к архиву сторонних пакетов и папке для распаковки
zip_path = os.path.join(script_path, 'amd64', 'Lib', 'site-packages.zip')
extract_path = os.path.dirname(zip_path)

# Распаковка сторонних пакетов
with ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

###############################################################################
# Создание файла настройки GigaChat

# Путь к файлу настройки GigaChat
config_path = os.path.join(script_path, 'gigakeys.ini')

# Проверка наличия файла настройки
if not os.path.exists(config_path):
    # Создание настройки
    config = configparser.ConfigParser()

    # Создание секции GIGACHAT
    config.add_section('GIGACHAT')
    config.set('GIGACHAT', 'authorization_key', '')
    config.set('GIGACHAT', 'session_id', str(uuid.uuid4()))

    # Запись настройки в  файл
    with open(config_path, 'w', encoding='utf-8') as config_file:
            config.write(config_file)

###############################################################################
print('''Программа успешно установлена.

Укажите ключ авторизации GigaChat в файле gigakeys.ini.'''
    )