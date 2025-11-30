"""
Обработчики меню и команд для бота.

Обрабатывает /start, /help и взаимодействия с главным меню.
"""

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from typing import Optional

from bot.states.product_states import ProductCardStates
from bot.utils.logger import get_logger
from bot.utils.constants import BotMessages

logger = get_logger(__name__)

router = Router()


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Создать клавиатуру главного меню.
    
    Returns:
        ReplyKeyboardMarkup: Главное меню с опциями.
    """
    buttons = [
        [KeyboardButton(text="📝 Создать из текста")],
        [KeyboardButton(text="📸 Создать из фото")],
        [KeyboardButton(text="ℹ️ Помощь")],
        [KeyboardButton(text="⚙️ Настройки")],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext) -> None:
    """
    Обработка команды /start.
    
    Инициализирует сессию пользователя и показывает главное меню.
    
    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    user_name = message.from_user.first_name or "User"
    
    await message.answer(
        BotMessages.WELCOME.format(name=user_name),
        reply_markup=get_main_menu()
    )
    
    # Установить начальное состояние
    await state.set_state(ProductCardStates.waiting_for_input)
    
    logger.info(f"User {message.from_user.id} started the bot")


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """
    Обработка команды /help.
    
    Предоставляет инструкции по использованию.
    
    Args:
        message: Входящее сообщение.
    """
    await message.answer(BotMessages.HELP_TEXT)
    logger.info(f"User {message.from_user.id} requested help")


@router.message(Command("settings"))
async def settings_handler(message: Message) -> None:
    """
    Обработка команды /settings.
    
    Показывает настройки пользователя (заглушка).
    
    Args:
        message: Входящее сообщение.
    """
    settings_text = """
⚙️ **Настройки:**

Текущие настройки:
- Язык: Русский
- Шаблон по умолчанию: Минимал
- Качество изображений: Высокое

(Управление настройками скоро будет доступно)
"""
    
    await message.answer(settings_text)
    logger.info(f"User {message.from_user.id} accessed settings")


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Обработка команды /cancel.
    
    Отменяет текущую операцию и возвращает в главное меню.
    
    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await state.clear()
    
    await message.answer(
        BotMessages.OPERATION_CANCELLED,
        reply_markup=get_main_menu()
    )
    
    await state.set_state(ProductCardStates.waiting_for_input)
    logger.info(f"User {message.from_user.id} cancelled current operation")


@router.message(F.text == "📝 Создать из текста")
async def create_from_text_handler(message: Message, state: FSMContext) -> None:
    """
    Обработка выбора опции текстового ввода.
    
    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await message.answer(BotMessages.TEXT_INPUT_PROMPT)
    
    await state.set_state(ProductCardStates.processing_text)
    logger.info(f"User {message.from_user.id} selected text input mode")


@router.message(F.text == "📸 Создать из фото")
async def create_from_photo_handler(message: Message, state: FSMContext) -> None:
    """
    Обработка выбора опции ввода фото.
    
    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    await message.answer(BotMessages.PHOTO_INPUT_PROMPT)
    
    await state.set_state(ProductCardStates.processing_image)
    logger.info(f"User {message.from_user.id} selected photo input mode")


@router.message(F.text == "ℹ️ Помощь")
async def help_button_handler(message: Message) -> None:
    """
    Обработка нажатия кнопки помощи.
    
    Args:
        message: Входящее сообщение.
    """
    await help_handler(message)


@router.message(F.text == "⚙️ Настройки")
async def settings_button_handler(message: Message) -> None:
    """
    Обработка нажатия кнопки настроек.
    
    Args:
        message: Входящее сообщение.
    """
    await settings_handler(message)
