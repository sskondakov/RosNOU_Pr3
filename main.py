import os
import sys

import json

import logging

from http.server import BaseHTTPRequestHandler, HTTPServer

from agents import BaseAIAgentManager, AIAgentMessage
from assistagents import TablesListAgent, TableDescriptionAgent, SQLAssistantAgent, CheckQueryAgent
from metadata import load_metadata
from utilities import set_main_folder, config_value, set_logging_level, main_logger

# Путm к папкам скрипта
script_path = os.path.dirname(os.path.abspath(__file__))

# Устанавливаем основную папку проекта
set_main_folder(script_path)

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

# HTTP-сервер
class MainHTTPServer(HTTPServer):
    def serve_forever(self):
        print(f'\nВеб-сервис запущен (порт: {self.server_address[1]}). Для остановки нажмите Ctrl+C...')

        try:
            super().serve_forever()

        except KeyboardInterrupt:
            print('\nВеб-сервис остановлен.')
            self.server_close()

# Старт веб-сервиса
def run():
    # Определение порта
    port = config_value(None, 'MAIN', 'port', None)
    if port is None:
        raise ValueError("Порт не задан")

    # Запуск веб-сервиса
    server_address = ('', port)
    httpd = MainHTTPServer(server_address, HTTPRequestHandler)
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
        print('''Программа запущена в режиме отладки. Параметры запуска:
 start - запуск веб-сервиса
 upload - загрузка метаданных
 
Выберите вариант работы:
 [1] Работа в консоли
 [2] Запуск веб-сервиса
 [3] Загрузка метаданных
 [4] Выход (Ctrl+C)'''
        )

        # Выбор варианта работы
        mode = None
        while mode is None:
            try:
                key = input('(1-4): ')
            except KeyboardInterrupt:
                key = '4'

            if key == '1':
                mode = 'console'
            elif key == '2':
                mode = 'web'
            elif key == '3':
                mode = 'upload'
            elif key == '4':
                mode = 'exit'

        if mode == 'console':
            is_working = True
            while is_working:
                try:
                    # Запрос описания задачи
                    prompt = input('\nОпишите задачу (Ctrl+C для выхода): ')
                    print('Ожидайте ответа...')

                    # Получения и вывод ответа
                    question = AIAgentMessage()
                    question.content = prompt
                    answer = AGENT_MANAGER.answer(question)
                    
                    print(f'\nОтвет:\n{answer.content}')

                except KeyboardInterrupt:
                    is_working = False

        elif mode == 'web':
            # Запуск веб-сервиса
            run()

        elif mode == 'upload':
            # Загрузка метаданных
            load_md()
            
        print('\nРабота завершена.')

    elif LOAD_MD_MODE:
        # Загрузка метаданных
        load_md()

    else:
        # Запуск веб-сервиса
        run()