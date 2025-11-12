from enum import Enum
import json

import os
import subprocess

import requests

from gigachat.models import Function
from gigachat.models.function_parameters import FunctionParameters

from agents import AIAgentMessage, BaseAIFunctions, BaseAIAgent
from gigagents import BaseGigaChatAIAgent
from metadata import tables_list, table_description
from utilities import main_folder, config_value, main_logger

# Перечисление дополнительных типов функций
class AIFunctions(Enum):
    tables_list = 'tables_list' # функция получения списка таблиц
    table_description = 'table_description' # функция получения описания таблицы по имени
    check_query = 'check_query' # функция проверки запроса

# Описание функций для API GigaChat
GIGACHAT_FUNCTIONS: dict = {
    AIFunctions.tables_list: Function(
        name=AIFunctions.tables_list.value,
        description='Возвращает список таблиц',
        parameters=FunctionParameters(properties={}, required=[]),
        return_parameters={
            'type': 'object',
            'properties': {
                'tables_list': {
                    'type': 'array',
                    'description': 'Cписок имен таблиц',
                    'items': {
                        'type': 'string'
                    }
                }
            }
        }
    ),
    AIFunctions.table_description: Function(
        name=AIFunctions.table_description.value,
        description='Возвращает описание таблицы по имени',
        parameters=FunctionParameters(
            properties={
                'table_name': {
                    'type': 'string',
                    'description': 'Имя таблицы'
                }
            },
            required=['table_name']
        ),
        return_parameters={
            'type': 'object',
            'properties': {
                'table_description': {
                    'type': 'string',
                    'description': 'Описание таблицы в формате JSON'
                }
            }
        }
    )
}

# Агент по составлению 1C-запросов
class SQLAssistantAgent(BaseGigaChatAIAgent):
    # Описание функций для API GigaChat
    _gigachat_functions = GIGACHAT_FUNCTIONS

    def __init__(self):
        # Получение логгер
        self._logger = main_logger()

        # Получение имени модели LLM
        model = config_value('GIGACHAT', 'model', None)
        if model is None:
            raise Exception("Не указан модель GigaChat")

        # Системный prompt
        system_prompt = '''Ты программист 1С 8.3

### Задача
Составить текст запроса для платформы 1С:Предприятие 8.3 по техническому заданию

### Требования
- Перед составлением запроса получи описание необходимых таблиц через функции.
- Убедиться, что есть описание всех необходимых таблиц.
- Формат ответа - только текст на языке запросов 1С 8.3, больше абсолютно ничего не добавляй.'''

        # Получение описания функций для API GigaChat
        function_tables_list = self._gigachat_functions[AIFunctions.tables_list]
        function_table_description = self._gigachat_functions[AIFunctions.table_description]

        # Инициализация как у базового класса
        super().__init__(system_prompt, model, [function_tables_list, function_table_description])

    # Возможность дать ответ
    def can_handle(self, question: AIAgentMessage) -> float:
        # Если это ответ на запрос функции - можем обработать
        if question.is_answer:
            if question.reply_to == self.__class__.__name__:
                return 1.0
        # Если это запрос от пользователя - можем обработать
        elif question.function == BaseAIFunctions.content:
            return 1.0
        return -1.0

    # Ответ на вопрос
    def answer(self, question: AIAgentMessage) -> AIAgentMessage:
        # Проверка возможности дать ответ
        if self.can_handle(question) == -1:
            raise Exception("Невозможно обработать запрос")

        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Запрос: {question}")

        # Если это запрос от пользователя - отвечаем
        if question.function == BaseAIFunctions.content:
            content = f'### Техническое задание:\n{question.content}'
            answer = self._answer(question.content, BaseAIFunctions.content)
        # Если это ответ от функции 'проверка запроса'
        elif question.function == AIFunctions.check_query:
            # Если запрос корректен - устанавливаем признак завершения работы
            if question.content == 'OK':
                answer = AIAgentMessage()
                answer.content = self._result
                answer.done = True
            # Просим исправить ошибку несколько раз
            elif self._trial_count < 3:
                content = f'Исправь ошибку:\n{question.content}'
                answer = self._answer(content, BaseAIFunctions.content)
            # Не получилось исправить - честно признаемся и завершаем работу
            else:
                answer = AIAgentMessage()
                answer.content = f'Не удается исправить ошибки, последний вариант:\n{self._result}'
                answer.done = True
        # Если это ответ на функций 'список таблиц' и 'описание таблицы по имени' - отвечаем
        elif question.function in [AIFunctions.tables_list, AIFunctions.table_description]:
            answer = self._answer(question.content, question.function.value, question.is_answer)
        else:
            raise Exception("Невозможно обработать запрос")

        # Получаем функцию AI-агента пл имени функции GigaChat
        if answer.function != BaseAIFunctions.content:
            answer.function = AIFunctions[answer.function]

        # Если не завершаем работу
        if not answer.done:
            # Если это ответ от для пользователя - запрашиваем функцию 'проверка запроса'
            if answer.function == BaseAIFunctions.content:
                answer.function = AIFunctions.check_query
                self._result = answer.content
                self._trial_count += 1
            # Если это запрос функции 'список таблиц' - чистим контент, он не нужен
            elif answer.function == AIFunctions.tables_list:
                answer.content = ''
            # Если это запрос функции 'описание таблицы по имени' - помещаем имя таблицы в контент
            elif answer.function == AIFunctions.table_description:
                answer.content = answer.content['table_name']
            else:
                raise Exception(f'Неизвестная функция: {answer.function}')

        # Мы либо отвечаем пользователю, либо вызываем функцию - фиксируем обратный адрес
        answer.reply_to = self.__class__.__name__

        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Ответ: {answer}")

        return answer

    # Очистка контекста
    def clear_context(self):
        super().clear_context()
        self._result = ''
        self._trial_count = 0

# Агент по составлению списка таблиц
# Функция: tables_list
class TablesListAgent(BaseAIAgent):
    def __init__(self):
        # Получение логгер
        self._logger = main_logger()

    # Возможность дать ответ
    def can_handle(self, question: AIAgentMessage) -> float:
        # Если это запрос нашей функции - отвечаем
        if question.function == AIFunctions.tables_list and not question.is_answer:
            return 1.0
        return -1.0

    # Ответ на вопрос
    def answer(self, question: AIAgentMessage) -> AIAgentMessage:
        # Проверка возможности дать ответ
        if self.can_handle(question) == -1:
            raise Exception("Невозможно обработать запрос")
        
        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Запрос: {question}")

        # Получение списка таблиц и формирование ответа на обратный адрес
        answer = AIAgentMessage()
        answer.function = AIFunctions.tables_list
        answer.content = json.dumps({'tables_list': tables_list()}, ensure_ascii=False)
        answer.is_answer = True
        answer.reply_to = question.reply_to

        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Ответ: {answer}")

        return answer

    # Очистка контекста
    def clear_context(self):
        pass

# Агент по описанию структуры таблицы
# Функция: table_description
class TableDescriptionAgent(BaseAIAgent):
    def __init__(self):
        # Получение логгер
        self._logger = main_logger()

    # Возможность дать ответ
    def can_handle(self, question: AIAgentMessage) -> float:
        # Если это запрос нашей функции - отвечаем
        if question.function == AIFunctions.table_description and not question.is_answer:
            return 1.0
        return -1.0

    # Ответ на вопрос
    def answer(self, question: AIAgentMessage) -> AIAgentMessage:
        # Проверка возможности дать ответ
        if self.can_handle(question) == -1:
            raise Exception("Невозможно обработать запрос")

        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Запрос: {question}")

        # Получение описания таблицы по имени
        json_string = table_description(question.content)
        if not json_string:
            description = 'Описание таблицы не найдено'
        else:
            description = json.loads(json_string)

        # Формирование ответа на обратный адрес
        answer = AIAgentMessage()
        answer.function = AIFunctions.table_description
        answer.content = json.dumps({'table_description': description}, ensure_ascii=False)
        answer.is_answer = True
        answer.reply_to = question.reply_to

        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Ответ: {answer}")

        return answer

    # Очистка контекста
    def clear_context(self):
        pass

# Агент по проверке таблиц
# Функция: check_query
class CheckQueryAgent(BaseAIAgent):
    def __init__(self):
        self._logger = main_logger()
        self.clear_context()

    # Обращение к веб-сервису проверки запроса
    def _check_query(self, query: str) -> str:
        # Получение адреса веб-сервиса проверки
        url = config_value('CHECK_QUERY', 'url', None)
        if url is None:
            raise Exception("Не указан адрес веб-сервиса проверки запроса")

        # Заголовок и тело запроса
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        body = {
            'query': query
        }

        try:
            # Сериализуем тело запроса JSON
            json_body = json.dumps(body, ensure_ascii=False)

            # Получаем ответ от веб-сервиса проверки
            response = requests.post(url, data=json_body, headers=headers, timeout=10)
            response.raise_for_status()

            # Десериализуем ответ из JSON
            body = json.loads(response.text)

            return body['result']

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при обращении к веб-сервису проверки запроса: {str(e)}")

    # Возможность дать ответ
    def can_handle(self, question: AIAgentMessage) -> float:
        # Если это запрос нашей функции - отвечаем
        if question.function == AIFunctions.check_query and not question.is_answer:
            return 1.0
        return -1.0

    # Ответ на вопрос
    def answer(self, question: AIAgentMessage) -> AIAgentMessage:
        # Проверка возможности дать ответ
        if self.can_handle(question) == -1:
            raise Exception("Невозможно обработать запрос")

        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Запрос: {question}")

        try:
            result = self._check_query(question.content)
            if not result:
                result = 'OK'
            elif 'Ожидается выражение "ВЫБРАТЬ"' in result:
                result = 'Нужен только текст на языке запросов 1С 8.3'

        except Exception as e:
            # Логгирование на уровне ошибки
            self._logger.error(f"Ошибка при проверке текста запроса:\n {str(e)}")

            # Базовая проверка
            if question.content.startswith('ВЫБРАТЬ'):
                result = 'OK'
            else:
                result = 'Нужен только текст на языке запросов 1С 8.3'

        # Формирование ответа на обратный адрес
        answer = AIAgentMessage()
        answer.function = question.function
        answer.content = result
        answer.is_answer = True
        answer.reply_to = question.reply_to

        # Логгирование на уровне отладки
        self._logger.debug(f"Объект: {self.__class__.__name__}\n Ответ: {answer}")

        return answer

    # Очистка контекста
    def clear_context(self):
        pass