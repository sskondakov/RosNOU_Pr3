import sqlite3
import json

import os

from utilities import config_value, main_folder

# Путь к база данных метаданных
def _metadata_db_path():
    # Имя файла базы наддых
    metadata_db_name = config_value(None, 'MAIN', 'metadata_db_name', None)
    if metadata_db_name is None:
        raise ValueError("Не указано имя базы данных метаданных")

    # Путь к файлу базы данных
    return os.path.join(main_folder(), metadata_db_name)

# Загрузка метаданных в базу данных
def load_metadata() -> bool:
    # Имя файла метаданных
    metadata_file_name = config_value(None, 'MAIN', 'metadata_file_name', None)
    if metadata_file_name is None:
        raise ValueError("Не указано имя файла метаданных")
    
    # Путь к файлу метаданных
    metadata_file_path = os.path.join(main_folder(), metadata_file_name)
    if not os.path.exists(metadata_file_path):
        return False

    # Получение пути к файлу базы данных и соединение
    metadata_db_path = _metadata_db_path()
    connection = sqlite3.connect(metadata_db_path)
    try:
        # Получение курсора базы данных
        cursor = connection.cursor()
        
        # Проверка наличия таблицы описания
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='table_descriptions'
        """)
        if cursor.fetchone() is None:
            # Создание таблицы описания
            cursor.execute("""
                CREATE TABLE table_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name VARCHAR(255) NOT NULL,
                    Description TEXT
                )
            """)
        else:
            # Очистка таблицы описания
            cursor.execute("DELETE FROM table_descriptions")
        
        # Загрузка метаданных из файла
        with open(metadata_file_path, 'r', encoding='utf-8') as metadata_file:
            json_string = metadata_file.read()
            metadata = json.loads(json_string)
        if metadata:
            # Подготовка списка кортежей с данными
            prepared_data = []
            for description in metadata:
                name = description['ИмяОбъекта']
                prepared_data.append((name, json.dumps(description, ensure_ascii=False)))

            # Загрузка данных в таблицу
            cursor.executemany("""
                INSERT INTO table_descriptions (Name, Description)
                VALUES (?, ?)
            """, prepared_data)
        
        # Фиксация транзакции
        connection.commit()
        
    except Exception as e:
        raise ValueError(f"Ошибка загрузки метаданных: {e}")

    finally:
        # Закрытие соединения с базой данных
        connection.close()

    return True

# Список таблиц метаданных
def tables_list() -> list[str]:
    result = []

    # Получение пути к файлу базы данных и соединение
    metadata_db_path = _metadata_db_path()
    connection = sqlite3.connect(metadata_db_path)
    try:
        # Получение курсора базы данных
        cursor = connection.cursor()
        
        # Получение имен таблиц порциями
        cursor.execute("SELECT Name FROM table_descriptions")
        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break
            for row in rows:
                result.append(row[0])

    except Exception as e:
        raise ValueError(f"Ошибка получения списка таблиц: {e}")

    finally:
        # Закрытие соединения с базой данных
        connection.close()

    return result

# Описание таблицы метаданных по имени
def table_description(table_name: str) -> str:
    result = ''

    # Получение пути к файлу базы данных и соединение
    metadata_db_path = _metadata_db_path()
    connection = sqlite3.connect(metadata_db_path)
    try:
        # Получение курсора базы данных
        cursor = connection.cursor()

        # Получение описания таблицы по имени
        cursor.execute("SELECT Description FROM table_descriptions WHERE Name=?", (table_name,))
        row = cursor.fetchone()
        if row:
            result = row[0]

    except Exception as e:
        raise ValueError(f"Ошибка получения описания таблицы: {e}")

    finally:
        # Закрытие соединения с базой данных
        connection.close()

    return result