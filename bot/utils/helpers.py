"""
Вспомогательные утилиты для работы с ответами AI.

Предоставляет функции проверки и парсинга для контента, сгенерированного AI.
"""

import json
import re
from typing import Optional, Dict, Any

from bot.utils.logger import get_logger

logger = get_logger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Извлечение JSON объекта из текста, который может содержать дополнительный контент.
    
    Обрабатывает случаи, когда AI возвращает JSON с markdown форматированием или дополнительным текстом.
    
    Args:
        text: Текст, потенциально содержащий JSON.
        
    Returns:
        Optional[Dict[str, Any]]: Разобранный JSON объект или None при ошибке извлечения.
    """
    # Сначала попытаться прямой парсинг
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Попытаться найти JSON в блоках кода
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(code_block_pattern, text)
    
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Попытаться найти JSON по фигурным скобкам
    json_start = text.find('{')
    json_end = text.rfind('}') + 1
    
    if json_start != -1 and json_end > json_start:
        try:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to extract JSON from text")
    
    return None


def validate_product_data(data: Dict[str, Any]) -> bool:
    """
    Проверка, что данные о продукте содержат необходимые поля.
    
    Args:
        data: Словарь данных о продукте.
        
    Returns:
        bool: True, если данные верны, иначе False.
    """
    # Как минимум, нужно название
    if not data.get('name') and not data.get('product_name'):
        return False
    
    return True


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Очистка текста для безопасного отображения и хранения.
    
    Args:
        text: Текст для очистки.
        max_length: Максимальная длина (обрезать, если длиннее).
        
    Returns:
        str: Очищенный текст.
    """
    if not text:
        return ""
    
    # Удалить излишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Обрезать при необходимости
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text


def format_price(price: Optional[str]) -> str:
    """
    Последовательное форматирование строки цены.
    
    Args:
        price: Строка цены.
        
    Returns:
        str: Отформатированная цена.
    """
    if not price:
        return ""
    
    # Очистить цену
    price = str(price).strip()
    
    # Если пустая строка после очистки
    if not price or price.lower() in ['null', 'none', 'n/a', 'не указана']:
        return ""
    
    # Извлечь числа из строки
    numbers = re.findall(r'\d+[\.,]?\d*', price)
    
    if numbers:
        # Взять первое число и форматировать
        num = numbers[0].replace(',', '.')
        
        # Проверить валюту в оригинальной строке
        if '₽' in price or 'руб' in price.lower() or 'rub' in price.lower():
            return f"{num}₽"
        elif '$' in price or 'usd' in price.lower():
            return f"${num}"
        elif '€' in price or 'eur' in price.lower():
            return f"€{num}"
        else:
            # По умолчанию рубли
            return f"{num}₽"
    
    return price
