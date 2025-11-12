from typing import Any, Union

import os

import configparser
import logging

# Путь к папке конфигурации
_MAIN_FOLDER_PATH = None

# Установка пути к папке конфигурации
def set_main_folder(path: str):
    global _MAIN_FOLDER_PATH
    _MAIN_FOLDER_PATH = path

# Путь к папке конфигурации
def main_folder() -> str:
    if _MAIN_FOLDER_PATH is None:
        raise Exception('Путь к папке AI-асистента не установлен')
    return _MAIN_FOLDER_PATH

# Значение из конфигурационного файла
def config_value(path: Union[str, None], section: str, key: str, fallback: Any = None) -> Union[str, int, float, bool, None]:
    # Чтение конфигурационного файла
    config_path = os.path.join(main_folder(), 'config.ini') if path is None else path
    parser = configparser.ConfigParser()
    parser.read(config_path)

    # Приведение представления значения к соответствующему типу
    try:
        value_str = parser.get(section, key, fallback=fallback)

        if value_str.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value_str.lower() in ('false', 'no', '0', 'off'):
            return False
            
        try:
            return int(value_str)
        except ValueError:
            pass
            
        try:
            return float(value_str)
        except ValueError:
            pass

        return value_str

    # Возврат значения по умолчанию при отсутствии раздела или ключа
    except (configparser.NoSectionError, configparser.NoOptionError):
        return fallback

# Экземпляр логгера
_MAIN_LOGGER = None
# Уровень логгирования
_LOGGING_LEVEL = logging.INFO

# Установка уровня логгирования
def set_logging_level(level: int):
    global _LOGGING_LEVEL
    _LOGGING_LEVEL = level

# Создание экземпляра логгера
def _create_logger():
    # Чтение имени файлов лога и установка параметров логгирования
    log_file_name = config_value(None, 'MAIN', 'log_file_name', 'events.log')
    logging.basicConfig(
        level=_LOGGING_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=os.path.join(main_folder(), log_file_name),
        filemode='a'
    )
    # Получение экземпляра логгера
    global _MAIN_LOGGER
    _MAIN_LOGGER = logging.getLogger('WebAssistant')

# Экземпляр логгера
def main_logger() -> logging.Logger:
    if _MAIN_LOGGER is None:
        _create_logger()
    return _MAIN_LOGGER