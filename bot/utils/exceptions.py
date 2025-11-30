"""
Пользовательские исключения для бота генератора карточек товаров.

Предоставляет специфические типы исключений для улучшенной обработки ошибок и отладки.
"""


class ProductCardBotException(Exception):
    """Базовое исключение для всех ошибок бота."""
    pass


class AIAnalysisError(ProductCardBotException):
    """Возникает при ошибке AI анализа."""
    pass


class InvalidProductDataError(ProductCardBotException):
    """Возникает когда данные о товаре невалидны или неполные."""
    pass


class TemplateRenderError(ProductCardBotException):
    """Возникает при ошибке рендеринга шаблона."""
    pass


class ImageProcessingError(ProductCardBotException):
    """Возникает при ошибке обработки изображения."""
    pass


class ConfigurationError(ProductCardBotException):
    """Возникает когда конфигурация невалидна."""
    pass


class APIError(ProductCardBotException):
    """Возникает при ошибке внешнего API запроса."""
    pass


class RateLimitError(APIError):
    """Возникает при превышении лимита частоты API запросов."""
    pass
