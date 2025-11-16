import os

from zipfile import ZipFile

# Путь к архиву сторонних пакетов и папке для распаковки
script_path = os.path.abspath(__file__)
zip_path = os.path.join(os.path.dirname(script_path), 'amd64', 'Lib', 'site-packages.zip')
extract_path = os.path.dirname(zip_path)

# Распаковка сторонних пакетов
with ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

print('Сторонние пакеты успешно распакованы.')