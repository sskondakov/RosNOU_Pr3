from enum import Enum
from typing import Any

from abc import ABC, abstractmethod

# Базовое перечисление типов функций
class BaseAIFunctions(Enum):
    content = 'content' # Контент - запрос от пользователя или ответ пользователю

# Сообщение AI-агента
class AIAgentMessage():
    def __init__(self):
        self.function: Any = BaseAIFunctions.content # Тип запрашиваемой функции
        self.content: Any = None # Контент запроса
        self._is_answer: bool = False # Это ответ на запрос функции
        self.reply_to: str = '' # Обратный адрес для ответа
        self.done: bool = False # Флаг завершения работы
        self.error: Exception = None # Ошибка

    # Техническое представление сообщения
    def __repr__(self):
        return f'''AIAgentMessage(
                function={self.function},
                content={self.content},
                is_answer={self._is_answer},
                reply_to={self.reply_to},
                done={self.done},
                error={self.error}
            )'''

    # Тип функции 'Контент' не может быть ответом
    @property
    def is_answer(self) -> bool:
        return self._is_answer and self.function != BaseAIFunctions.content

    # Установка флага 'ответ'
    @is_answer.setter
    def is_answer(self, value: bool):
        self._is_answer = value

# Базовый абстрактный AI-агент
class BaseAIAgent(ABC):
    # Возможность дать ответ
    @abstractmethod
    def can_handle(self, question: AIAgentMessage) -> float:
        pass

    # Ответ на вопрос
    @abstractmethod
    def answer(self, question: AIAgentMessage) -> AIAgentMessage:
        pass

    # Очистка контекста
    @abstractmethod
    def clear_context(self):
        pass

# Базовый менеджер AI-агентов
class BaseAIAgentManager():
    def __init__(self, agents: list):
        self._agents: list = agents

    # Добавление агента
    def _add_agent(self, agent: BaseAIAgent):
        self._agents.append(agent)

    # Удаление агента
    def _del_agent(self, agent: BaseAIAgent):
        self._agents.remove(agent)

    # Поиск исполнителя
    def _find_contractor(self, message: AIAgentMessage) -> BaseAIAgent:
        # Исполнителем будет агент с максимальным уровнем уверенности
        best_agent = None
        best_confidence = -1.0 # стандартный диапазон: 0.0 - 1.0
        for agent in self._agents:
            # Получаем и проверем уровень уверенности AI-агента
            confidence = agent.can_handle(message)
            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = agent

        if best_agent is None or best_confidence < 0.0:
            return None
        return best_agent

    # Ответ на вопрос
    def answer(self, message: AIAgentMessage) -> AIAgentMessage:
        # Цикл поиска ответа
        while not message.done:
            # Поиск исполнителя функции
            agent = self._find_contractor(message)
            if agent is None:
                message.error = ValueError("Не удалось найти исполнителя.")
                return message
            # Получение ответа
            message = agent.answer(message)
        return message

    # Очистка контекста
    def clear_context(self):
        # Очистка контекста AI-агентоа
        for agent in self._agents:
            agent.clear_context()