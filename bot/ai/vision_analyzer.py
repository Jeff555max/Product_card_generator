"""
Модуль анализатора изображений для извлечения информации о продукте на основе изображений.

Обрабатывает анализ изображений продуктов с использованием возможностей AI компьютерного зрения.
"""

import json
import logging
from typing import Optional
import aiohttp

from bot.ai.client import OpenRouterClient
from bot.ai.text_analyzer import ProductInfo
from bot.utils.logger import get_logger
from bot.utils.helpers import extract_json_from_text, sanitize_text, format_price
from bot.prompts.product_prompts import ProductPrompts

logger = get_logger(__name__)


class VisionAnalyzer:
    """
    Анализатор изображений продуктов с использованием AI компьютерного зрения.
    
    Извлекает информацию о продукте из изображений с помощью моделей компьютерного зрения OpenRouter.
    Следует принципу единой ответственности.
    """
    
    def __init__(self, ai_client: OpenRouterClient):
        """
        Инициализация анализатора изображений.
        
        Args:
            ai_client: OpenRouter клиент для AI операций.
        """
        self.ai_client = ai_client
    
    async def download_and_encode_image(self, image_url: str) -> Optional[str]:
        """
        Загрузить изображение и преобразовать в base64 для API.
        
        Args:
            image_url: URL изображения для загрузки.
            
        Returns:
            Optional[str]: Изображение, закодированное в base64 или None при ошибке загрузки.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        import base64
                        return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to download image: {str(e)}")
        
        return None
    
    async def analyze_product_image(self, image_url: str) -> ProductInfo:
        """
        Анализ изображения продукта и извлечение информации.
        
        Args:
            image_url: URL изображения продукта.
            
        Returns:
            ProductInfo: Извлеченная информация о продукте из изображения.
        """
        try:
            logger.info(f"Analyzing image from URL: {image_url}")
            
            # Получить анализ изображения от AI используя структурированный промпт
            ai_response = await self.ai_client.analyze_image(
                image_url=image_url,
                prompt=ProductPrompts.EXTRACT_FROM_IMAGE
            )
            
            # Разобрать ответ
            product_info = self._parse_vision_response(ai_response)
            
            logger.info(f"Successfully analyzed image: {product_info.name}")
            return product_info
        
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return ProductInfo()
    
    def _parse_vision_response(self, response: str) -> ProductInfo:
        """
        Разбор ответа AI анализа изображения.
        
        Args:
            response: Ответ AI модели с анализом продукта.
            
        Returns:
            ProductInfo: Разобранная информация о продукте.
        """
        data = extract_json_from_text(response)
        
        if data:
            # Извлечь цену из разных возможных полей
            price = data.get('price') or data.get('estimated_price_range') or data.get('estimated_price')
            
            return ProductInfo(
                name=sanitize_text(data.get('product_name') or data.get('name')),
                category=sanitize_text(data.get('category')),
                color=sanitize_text(data.get('color')),
                size=sanitize_text(data.get('size')),
                description=sanitize_text(data.get('description'), max_length=500),
                price=price if price else None,  # Не форматировать, использовать как есть
                other_features=data.get('features') or data.get('other_features', {})
            )
        
        logger.warning("Failed to parse vision response as JSON")
        return ProductInfo()
    
    async def extract_text_from_image(self, image_url: str) -> str:
        """
        Извлечение видимого текста из изображения продукта (OCR).
        
        Args:
            image_url: URL изображения.
            
        Returns:
            str: Извлеченный текст из изображения.
        """
        try:
            logger.info("Extracting text from image...")
            
            # Использовать AI для извлечения видимого текста
            extracted_text = await self.ai_client.analyze_image(
                image_url=image_url,
                prompt=ProductPrompts.EXTRACT_TEXT_FROM_IMAGE
            )
            
            return extracted_text
        
        except Exception as e:
            logger.error(f"Failed to extract text from image: {str(e)}")
            return ""
