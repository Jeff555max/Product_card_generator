"""
Состояния конечного автомата для взаимодействия с ботом.

Определяет все состояния для взаимодействия пользователя с ботом согласно паттерну конечного автомата.
"""

from aiogram.fsm.state import State, StatesGroup


class ProductCardStates(StatesGroup):
    """
    Состояния FSM для рабочего процесса генерации карточек товаров.
    
    Определяет последовательность состояний, через которые проходит пользователь при генерации карточки товара.
    """
    
    # Начальное состояние
    waiting_for_input = State()
    
    # Состояния обработки ввода
    processing_text = State()
    processing_image = State()
    
    # Состояния уточнения информации
    waiting_for_missing_info = State()
    confirming_extracted_data = State()
    
    # Состояние выбора шаблона
    selecting_template = State()
    
    # Состояния настройки
    waiting_for_customization = State()
    preview_card = State()
    
    # Конечное состояние
    card_generated = State()


class AdminStates(StatesGroup):
    """
    Состояния FSM для административных операций.
    
    Используется для административных функций, таких как статистика, управление пользователями и т.д.
    """
    
    waiting_for_admin_command = State()
    processing_analytics = State()
