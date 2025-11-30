"""
Утилиты логирования для бота генератора карточек товаров.

Предоставляет централизованную конфигурацию логирования и создание логгеров.
"""

import logging
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Получить экземпляр логгера с указанным именем.
    
    Args:
        name: Имя логгера (обычно __name__ из вызывающего модуля).
        
    Returns:
        logging.Logger: Настроенный экземпляр логгера.
    """
    return logging.getLogger(name)


class LoggerAdapter:
    """
    Адаптер для единообразного логирования во всем приложении.
    
    Предоставляет методы для обычных операций логирования с контекстной информацией.
    """
    
    def __init__(self, logger: logging.Logger, context: Optional[dict] = None):
        """
        Инициализация адаптера логгера.
        
        Args:
            logger: Базовый экземпляр логгера.
            context: Дополнительный контекст для включения в сообщения логов.
        """
        self.logger = logger
        self.context = context or {}
    
    def _format_message(self, message: str) -> str:
        """
        Отформатировать сообщение с контекстной информацией.
        
        Args:
            message: Сообщение для форматирования.
            
        Returns:
            str: Отформатированное сообщение.
        """
        if self.context:
            context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"[{context_str}] {message}"
        return message
    
    def info(self, message: str) -> None:
        """Записать информационное сообщение."""
        self.logger.info(self._format_message(message))
    
    def debug(self, message: str) -> None:
        """Записать отладочное сообщение."""
        self.logger.debug(self._format_message(message))
    
    def warning(self, message: str) -> None:
        """Записать предупреждение."""
        self.logger.warning(self._format_message(message))
    
    def error(self, message: str) -> None:
        """Записать сообщение об ошибке."""
        self.logger.error(self._format_message(message))
    
    def critical(self, message: str) -> None:
        """Записать критическое сообщение."""
        self.logger.critical(self._format_message(message))
