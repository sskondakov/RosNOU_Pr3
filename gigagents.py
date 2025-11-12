from collections import deque

import os

from gigachat import GigaChat
import gigachat.context
from gigachat.models import Chat, Messages, MessagesRole

from utilities import config_value, main_folder

from agents import AIAgentMessage, BaseAIFunctions, BaseAIAgent

# История сообщений GigaChat
class GigaChatHistory():
    def __init__(self, system_prompt: str):
        # Ограничение максимального размера контекста
        max_context_length = config_value(None, 'GIGACHAT', 'max_context_length', None)
        if max_context_length is None:
            raise Exception('Максимальная длина контекста GigaChat не установлена')
        self._max_context_length = max_context_length

        # Первое сообщение всегда системный промпт
        message = Messages(
            role=MessagesRole.SYSTEM,
            content=system_prompt
        )
        self._messages = deque([message])

    # Количество сообщений в истории для функции len()
    def __len__(self) -> int:
        return len(self._messages)

    # Размер контекста как сумма длины всех сообщений
    def _context_length(self) -> int:
        return sum(len(message.content) for message in self._messages)

    # Ограничение максимального размера контекста
    def _enforce_context_limit(self):
        # Удаление самого старого сообщение (кроме системного промта)
        while len(self) > 2 and self._context_length() > self._max_context_length:
            del self._messages[1]

        # Контроль: втрое сообщение должно быть от пользователя
        if len(self) > 2 and self._messages[1].role != MessagesRole.USER:
            del self._messages[1]

    # Добавление любого сообщения GigaChat
    def add_message(self, message: Messages):
        # Добавление сообщения
        self._messages.append(message)
        # Контроль размера контекста
        self._enforce_context_limit()

    # Добавление сообщения пользователя
    def add_user_content(self, content: str) -> Messages:
        # Новое сообщения GigaChat
        message = Messages(
            role=MessagesRole.USER,
            content=content
        )
        self.add_message(message)

        return message

    # Добавление системного промта
    def add_assistant_content(self, content: str) -> Messages:
        # Новое сообщения GigaChat
        message = Messages(
            role=MessagesRole.ASSISTANT,
            content=content
        )
        self.add_message(message)

        return message

    # Добавление сообщения функции
    def add_function_content(self, content: str, function: str) -> Messages:
        # Новое сообщения GigaChat
        message = Messages(
            role=MessagesRole.FUNCTION,
            content=content,
            name=function
        )
        self.add_message(message)

        return message

    # Список сообщений
    def messages(self) -> list[Messages]:
        return list(self._messages)

# Базовый класс GigaChat AI-агента
class BaseGigaChatAIAgent(BaseAIAgent):
    def __init__(self, system_prompt: str, model: str, functions: list):
        # Личные данные храним в отдельном файле
        config_path = os.path.join(main_folder(), 'gigakeys.ini')

        # Ключ авторизации GigaChat
        authorization_key = config_value(config_path, 'GIGACHAT', 'authorization_key', None)
        if authorization_key is None:
            raise Exception('Ключ авторизации GigaChat не установлен')
        self._authorization_key = authorization_key
        
        # Заголовки соединения с GigaChat: идентификатор сессия, ...
        session_id = config_value(config_path,'GIGACHAT', 'session_id', None)
        if session_id is None:
            raise Exception('Идентификатор сессия GigaChat не установлен')
        self._headers = {"X-Session-ID": session_id}

        # Параметры GigaChat
        self._model = model
        self._system_prompt = system_prompt
        self._functions = functions

        # Очистка контекста
        self.clear_context()

    # Ответ на вопрос
    def _answer(self, content: str, function: str, is_answer: bool = False) -> AIAgentMessage:
        # Добавление резултата функции в чат
        if is_answer:
            self._chat_history.add_function_content(content, function)

        # Добавление сообщения пользователя в чат
        else:
            self._chat_history.add_user_content(content)
        
        # Отправка сообщений чата в GigaChat
        with GigaChat(
            credentials=self._authorization_key,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        ) as giga:
            gigachat.context.session_id_cvar.set(self._headers.get("X-Session-ID"))

            chat = Chat(
                messages=self._chat_history.messages(),
                model=self._model,
                functions=self._functions
            )
            response = giga.chat(chat)

        # Добавление сообщения ассистента в чат
        chat_message = response.choices[0].message
        self._chat_history.add_message(chat_message)

        answer = AIAgentMessage()
        # Помещение ответа в сообщение
        if chat_message.function_call is None:
            answer.content = chat_message.content.strip()

        # Помещение параметров и имени функции в сообщение
        else:
            answer.function = chat_message.function_call.name
            answer.content = chat_message.function_call.arguments

        return answer

    # Возможность дать ответ
    def can_handle(self, question: AIAgentMessage) -> float:
        if question.function == BaseAIFunctions.content:
            return 1.0
        return 0.0

    # Ответ на вопрос
    def answer(self, question: AIAgentMessage) -> AIAgentMessage:
        # Получение ответа на вопрос
        answer = self._answer(question.content, question.function, question.is_answer)
        # По умолчанию обычный контент (не вызов функции) провоцирует завершение работы
        if answer.function == BaseAIFunctions.content:
            answer.done = True
        return answer

    # Очистка контекста
    def clear_context(self):
        # Новая история чата с GigaChat
        self._chat_history = GigaChatHistory(self._system_prompt)