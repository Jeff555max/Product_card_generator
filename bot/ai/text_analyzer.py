"""
Модуль текстового анализатора для извлечения информации о продукте.

Обрабатывает парсинг и анализ текстовых описаний для извлечения атрибутов продукта.
"""

import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from bot.ai.client import OpenRouterClient
from bot.utils.logger import get_logger
from bot.utils.helpers import extract_json_from_text, sanitize_text, format_price
from bot.prompts.product_prompts import ProductPrompts
from bot.utils.constants import AIConfig

logger = get_logger(__name__)


@dataclass
class ProductInfo:
    """
    Класс данных, представляющий извлеченную информацию о продукте.
    
    Attributes:
        name: Название продукта.
        price: Цена продукта.
        description: Описание продукта.
        category: Категория продукта.
        color: Цвет продукта.
        size: Размер продукта.
        other_features: Дополнительные характеристики продукта в виде словаря.
    """
    name: Optional[str] = None
    price: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    other_features: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать информацию о продукте в словарь."""
        return asdict(self)
    
    def has_required_fields(self) -> bool:
        """Проверить, содержит ли продукт минимально необходимую информацию."""
        return bool(self.name and (self.price or self.description))


class TextAnalyzer:
    """
    Анализатор текстовых описаний продуктов.
    
    Извлекает информацию о продукте из текста с использованием AI моделей.
    Следует принципу единой ответственности.
    """
    
    def __init__(self, ai_client: OpenRouterClient):
        """
        Инициализация текстового анализатора.
        
        Args:
            ai_client: OpenRouter клиент для AI операций.
        """
        self.ai_client = ai_client
    
    async def extract_product_info(self, text: str) -> ProductInfo:
        """
        Извлечение информации о продукте из текстового описания.
        
        Args:
            text: Текст описания продукта.
            
        Returns:
            ProductInfo: Извлеченная информация о продукте.
        """
        try:
            logger.info(f"Analyzing text: {text[:100]}...")
            
            # Подготовить промпт с текстом
            prompt = ProductPrompts.EXTRACT_FROM_TEXT.format(text=text)
            
            # Использовать AI для извлечения структурированной информациированной информации
            ai_response = await self.ai_client.analyze_text(
                text=text,
                prompt=prompt
            )
            
            # Разобрать ответ AI
            product_info = self._parse_ai_response(ai_response)
            
            logger.info(f"Successfully extracted product: {product_info.name}")
            return product_info
        
        except Exception as e:
            logger.error(f"Error extracting product info: {str(e)}")
            # Вернуть частичную информацию из текста при сбое AI
            return self._extract_basic_info(text)
    
    def _parse_ai_response(self, response: str) -> ProductInfo:
        """
        Разбор ответа AI и извлечение информации о продукте.
        
        Args:
            response: Ответ AI модели (должен содержать JSON).
            
        Returns:
            ProductInfo: Разобранная информация о продукте.
        """
        data = extract_json_from_text(response)
        
        if data:
            return ProductInfo(
                name=sanitize_text(data.get('name')),
                price=format_price(data.get('price')),
                description=sanitize_text(data.get('description'), max_length=500),
                category=sanitize_text(data.get('category')),
                color=sanitize_text(data.get('color')),
                size=sanitize_text(data.get('size')),
                other_features=data.get('other_features', {})
            )
        
        logger.warning("Failed to parse AI response as JSON")
        return ProductInfo()
    
    def _extract_basic_info(self, text: str) -> ProductInfo:
        """
        Извлечение базовой информации о продукте с использованием простых эвристик.
        
        Откат к базовому извлечению при сбое AI.
        
        Args:
            text: Описание продукта.
            
        Returns:
            ProductInfo: Базовая извлеченная информация.
        """        
        # Простое извлечение на основе регулярных выражений в качестве запасного варианта
        lines = text.split('\n')
        
        product_info = ProductInfo(
            name=lines[0] if lines else "Product",
            description='\n'.join(lines[1:]) if len(lines) > 1 else text
        )
        
        # Попытаться найти цену (искать знаки валюты и слова)
        import re
        # Ищем цены с различными форматами: 3400₽, 3400 руб, $100, 100$, €50
        price_patterns = [
            r'(\d+[\s]*[₽рублейруб\.]+)',  # 3400₽, 3400 руб, 3400 рублей
            r'(цена[:\s-]*\d+[\s]*[₽рублейруб\.]*)',  # цена 3400, цена: 3400₽
            r'([\$€£]\s*\d+[\.,]?\d*)',  # $100, €50
            r'(\d+[\.,]?\d*\s*[\$€£])',  # 100$, 50€
            r'(\d+\s*(?:руб|рублей|₽))',  # 3400 руб
        ]
        
        for pattern in price_patterns:
            price_match = re.search(pattern, text, re.IGNORECASE)
            if price_match:
                price_str = price_match.group()
                # Извлечь только числа
                numbers = re.findall(r'\d+', price_str)
                if numbers:
                    product_info.price = f"{numbers[0]}₽"
                    break
        
        return product_info
    
    async def suggest_improvements(self, description: str) -> str:
        """
        Получить предложения AI по улучшению описания продукта.
        
        Args:
            description: Текущее описание продукта.
            
        Returns:
            str: Предложения по улучшению.
        """
        try:
            logger.info("Requesting improvement suggestions...")
            
            prompt = ProductPrompts.SUGGEST_IMPROVEMENTS.format(description=description)
            
            suggestions = await self.ai_client.generate_completion(
                prompt=prompt,
                temperature=AIConfig.TEMPERATURE_SUGGESTIONS,
                max_tokens=AIConfig.MAX_TOKENS_SUGGESTIONS
            )
            
            return suggestions
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return "Unable to generate suggestions at this time."
