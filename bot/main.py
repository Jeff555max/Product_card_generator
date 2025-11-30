"""
Основной модуль бота и точка входа.

Инициализирует и запускает Telegram бот генератора карточек товаров.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.config import Config
from bot.handlers import menu, description, photo
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    """
    Установить команды бота, отображаемые в меню.
    
    Args:
        bot: Экземпляр бота.
    """
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Показать справку"),
        BotCommand(command="settings", description="Настройки"),
        BotCommand(command="cancel", description="Отменить операцию"),
    ]
    
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully")


async def on_startup(bot: Bot) -> None:
    """
    Обработка запуска бота.
    
    Args:
        bot: Экземпляр бота.
    """
    logger.info("Bot is starting up...")
    await set_bot_commands(bot)
    logger.info("Bot is ready!")


async def on_shutdown(bot: Bot) -> None:
    """
    Обработка завершения работы бота.
    
    Args:
        bot: Экземпляр бота.
    """
    logger.info("Bot is shutting down...")


async def main() -> None:
    """
    Основная точка входа для бота.
    
    Проверяет конфигурацию, инициализирует бот и диспетчер,
    регистрирует обработчики и запускает поллинг.
    """
    # Проверить конфигурацию
    if not Config.validate():
        logger.error("Configuration validation failed!")
        return
    
    # Настроить логирование и директории
    Config.setup_logging()
    Config.create_directories()
    
    logger.info("Starting Product Card Generator Bot...")
    logger.info(f"Bot token: {Config.TELEGRAM_BOT_TOKEN[:10]}...")
    logger.info(f"Model: {Config.MODEL_NAME}")
    logger.info(f"Debug mode: {Config.DEBUG}")
    
    # Инициализировать бот и диспетчер
    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    # Зарегистрировать роутеры (обработчики)
    dp.include_router(menu.router)
    dp.include_router(description.router)
    dp.include_router(photo.router)
    
    # Настроить обработчики запуска и завершения
    async def startup_wrapper():
        await on_startup(bot)
    
    async def shutdown_wrapper():
        await on_shutdown(bot)
    
    dp.startup.register(startup_wrapper)
    dp.shutdown.register(shutdown_wrapper)
    
    # Запустить поллинг
    try:
        logger.info("Bot is polling for updates...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Bot was interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        await bot.session.close()
        logger.info("Bot session closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
