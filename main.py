import json

import os
import sys

import logging

from http.server import BaseHTTPRequestHandler, HTTPServer

from agents import BaseAIAgentManager, AIAgentMessage
from assistagents import TablesListAgent, TableDescriptionAgent, SQLAssistantAgent, CheckQueryAgent
from metadata import load_metadata
from utilities import set_main_folder, config_value, set_logging_level, main_logger

# Путь к папке файлов AI-асистента
set_main_folder(os.path.dirname(os.path.abspath(__file__)))

# Определение режима запуска
DEBUG_MODE = True
LOAD_MD_MODE = False
for arg in reversed(sys.argv):
    if arg == 'start':
        DEBUG_MODE = False
    if arg == 'load_md':
        LOAD_MD_MODE = True

# Установка уровня логгирования
if DEBUG_MODE:
    set_logging_level(logging.DEBUG)

# Менеджер AI-агентов
class AIAgentManager(BaseAIAgentManager):
    def __init__(self):
        # Инициализация AI-агентов
        super().__init__(
            [
                TablesListAgent(),
                TableDescriptionAgent(),
                SQLAssistantAgent(),
                CheckQueryAgent()
            ]
        )
# Экземпляр менеджера AI-агентов
AGENT_MANAGER = AIAgentManager()

# Обработчик http-запросов
class HTTPRequestHandler(BaseHTTPRequestHandler):
    _logger = main_logger() # Экземпляр логгера
    _agent_manadger = AGENT_MANAGER # Экземпляр менеджера AI-агентов

    # Десериализация JSON-строки
    def _message_from_json(self, json_string):
        try:
            message = json.loads(json_string)
            return message

        except json.JSONDecodeError:
            self._logger.error(f"Ошибка декодирования JSON: {json_string}")
            return None

    # Сериализация в JSON-строку
    def _json_from_message(self, message):
        return json.dumps(message).encode()

    # Обрабатка запросов
    def _response(self, request):
        # Новое сообщения для AI-агентов
        question = AIAgentMessage()
        question.content = request['prompt']

        # Очистка контекста и получения ответа
        self._agent_manadger.clear_context()
        answer = self._agent_manadger.answer(question)

        return {'response': answer.content}

    # Обрабатчик POST-запросов
    def do_POST(self):
        # Чтение входящего запроса
        content_length = int(self.headers['Content-Length'])
        json_string = self.rfile.read(content_length)

        # Десериализация из JSON-строки и получение ответа
        request = self._message_from_json(json_string)
        response = self._response(request)

        # Формированиея статуса и заголовков
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Cериализация в JSON-строку и отправка ответа
        json_string = self._json_from_message(response)
        self.wfile.write(json_string)

    # Обрабатчик GET-запросов
    def do_GET(self):
        # Формированиея статуса и заголовков
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        # Отправка HTML-страницы
        self.wfile.write(b'<h1><b>SQL-assistant works.</b></h1>')

# Старт веб-сервиса
def run(server_class=HTTPServer, handler_class=HTTPRequestHandler):
    # Определение порта
    port = config_value('MAIN', 'port', None)
    if port is None:
        raise ValueError("Порт не задан")

    print(f'''\nДля проверки запуска веб-севриса введите в браузере строку: localhost:{port},
вы должны увидеть надпись: SQL-assistant works.

Для проверки работы SQL-ассистента отправьте по адресу localhost:{port}
POST запрос в формате JSON в кодировке UTF-8: {{"prompt": "Описание задачи"}}

Веб-сервис запущен (порт: {port})...'''
    )

    # Запуск веб-сервиса
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

# Загрузка метаданных
def load_md():
    print('\nЗагрузка метаданных в базу данных...')
    if load_metadata():
        print('Метаданные успешно загружены.')
    else:
        print('Файл метаданных не найден.')

# Код главного скрипта
if __name__ == '__main__':
    if DEBUG_MODE:
        # Выбор режима работы
        print('''Веб-сервис запущен в режиме отладки. Параметры запуска:
 start - запуск веб-сервиса в "боевом" режиме
 upload - загрузка метаданных в базу данных

Веб-сервис разработан для помощи продвинутым аналитикам в формирования запросов
на языке запросов 1С:Предприятие 8.
Для формирования файла метаданных необходимо воспользоваться внешней обработкой
DumpMetadata.epf. Пример запроса к веб-сервису:
 headers:
  Content-Length: 53
  Content-type: application/json
 body: 
  {"prompt": "Все покупки за неделю"}
В состав поставки включен файл метаданных metadata1.json на основе конфигурации
"Учет движения средств" книги "Язык запросов "1С:Предприятие 8".

Выберите режим работы:
 [1] Отладка в консоли
 [2] Отладка веб-сервиса
 [3] Выход'''
        )

        key = input('(1-3): ')
        if key == '1':
            # Загрузка метаданных
            load_md()

            is_working = True
            while is_working:
                # Запрос описания задачи
                prompt = input('\nОпишите задачу на формирование запроса: ')
                print('\nОжидайте ответа...')

                # Получения и вывод ответа
                question = AIAgentMessage()
                question.content = prompt
                answer = AGENT_MANAGER.answer(question)
                
                print(f'\nОтвет:\n{answer.content}')

                # Запрос на выход
                key = input('\nВыход? (y/n): ')
                if key == 'y':
                    is_working = False

            print('\nРабота завершена.')

        elif key == '2':
            # Запуск веб-сервиса
            run()

        else:
            print('\nРабота завершена.')

    elif LOAD_MD_MODE:
        # Загрузка метаданных
        load_md()

    else:
        # Запуск веб-сервиса
        run()