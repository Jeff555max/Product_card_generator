"""
Модуль конфигурации для бота генератора карточек товаров.

Этот модуль обрабатывает загрузку и управление конфигурацией из переменных окружения.
Использует python-dotenv для безопасного управления учетными данными.
"""

import logging
import os
from dotenv import load_dotenv

# Загрузить переменные окружения из .env файла
load_dotenv(".env")


class Config:
    """
    Основной класс конфигурации приложения.
    
    Все конфиденциальные учетные данные и настройки загружаются из переменных окружения.
    """
    
    # Конфигурация Telegram бота
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Конфигурация OpenRouter API
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "google/gemini-2.5-flash")
    IMAGE_MODEL_NAME: str = os.getenv("IMAGE_MODEL_NAME", "openai/dall-e-3")
    
    # Настройки приложения
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Настройки генерируемых файлов
    CARDS_DIR: str = "generated_cards"
    CACHE_DIR: str = "cache"
    LOGS_DIR: str = "logs"
    
    @classmethod
    def validate(cls) -> bool:
        """
        Проверка, что все необходимые переменные конфигурации установлены.
        
        Returns:
            bool: True, если все необходимые переменные установлены, иначе False.
        """
        required_vars = ["TELEGRAM_BOT_TOKEN", "OPENROUTER_API_KEY"]
        missing_vars = [var for var in required_vars if not getattr(cls, var, None)]
        
        if missing_vars:
            logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    @classmethod
    def setup_logging(cls) -> None:
        """
        Настройка логирования для приложения.
        
        Настраивает логирование с указанным уровнем и создает директорию logs,
        если она не существует.
        """
        # Создать директорию logs, если она не существует
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(cls.LOGS_DIR, 'bot.log')),
                logging.StreamHandler()
            ]
        )
    
    @classmethod
    def create_directories(cls) -> None:
        """
        Создание необходимых директорий для приложения.
        
        Создает директории для генерируемых карточек, кэша и логов, если они не существуют.
        """
        for directory in [cls.CARDS_DIR, cls.CACHE_DIR, cls.LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)


def get_config() -> Config:
    """
    Получить экземпляр конфигурации приложения.
    
    Returns:
        Config: Экземпляр конфигурации.
    """
    return Config
