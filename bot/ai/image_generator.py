"""
Модуль для генерации изображений товаров с использованием AI.

Использует OpenRouter API для доступа к моделям генерации изображений (Gemini 2.5 Flash Image).
"""

import logging
import aiohttp
import asyncio
import base64
import os
import re
from typing import Optional, Dict, Any

from bot.config import Config
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class ImageGenerator:
    """
    Генератор изображений товаров с использованием OpenRouter API.
    
    Использует Gemini 2.5 Flash Image (Nano Banana) через chat completions API.
    """
    
    def __init__(self, api_key: str, model_name: str):
        """
        Инициализация генератора изображений.
        
        Args:
            api_key: Ключ OpenRouter API.
            model_name: Модель для генерации изображений (например, 'google/gemini-2.5-flash-image').
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://openrouter.ai/api/v1"
        self.max_retries = 3
        self.retry_delay = 2
    
    async def generate_product_image(
        self,
        product_name: str,
        category: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        style: str = "realistic product photography"
    ) -> Optional[str]:
        """
        Генерация изображения товара на основе его характеристик.
        
        Args:
            product_name: Название товара.
            category: Категория товара.
            color: Цвет товара.
            size: Размер товара.
            style: Стиль изображения.
            
        Returns:
            Optional[str]: Base64 data URL сгенерированного изображения, или None при ошибке.
        """
        # Формируем детальный промпт для генерации
        prompt = self._build_prompt(product_name, category, color, size, style)
        
        logger.info(f"Generating image with prompt: {prompt[:100]}...")
        
        try:
            image_data = await self._generate_image_via_chat(prompt)
            if image_data:
                logger.info(f"Image generated successfully")
                return image_data
            else:
                logger.warning("Image generation returned None")
                return None
        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            return None
    
    def _build_prompt(
        self,
        product_name: str,
        category: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        style: str = "realistic product photography"
    ) -> str:
        """
        Построение промпта для генерации изображения.
        
        Args:
            product_name: Название товара.
            category: Категория товара.
            color: Цвет товара.
            size: Размер товара.
            style: Стиль изображения.
            
        Returns:
            str: Промпт для модели генерации.
        """
        parts = [f"Generate a professional {style} of {product_name}"]
        
        if color:
            parts.append(f"in {color} color")
        
        if size:
            parts.append(f"{size} size")
        
        if category:
            parts.append(f"({category})")
        
        # Добавляем технические детали для лучшего качества
        parts.append(
            "on a clean white or light gradient background, "
            "studio lighting, high resolution, "
            "centered composition, no text or watermarks, "
            "product only, professional e-commerce style"
        )
        
        return ", ".join(parts)
    
    async def _generate_image_via_chat(self, prompt: str) -> Optional[str]:
        """
        Генерация изображения через chat completions API.
        
        Gemini 2.5 Flash Image генерирует изображения через стандартный chat API
        и возвращает base64-encoded изображение в ответе.
        
        Args:
            prompt: Промпт для генерации.
            
        Returns:
            Optional[str]: Base64 data URL изображения или None.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Jeff555max/Product_card_generator",
            "X-Title": "Product Card Generator",
            "Content-Type": "application/json"
        }
        
        # Используем chat completions API для Gemini 2.5 Flash Image
        # ВАЖНО: нужен параметр modalities для генерации изображений
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"],
            "max_tokens": 4096
        }
        
        url = f"{self.base_url}/chat/completions"
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return self._extract_image_from_response(result)
                        elif response.status == 429:
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited. Waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            error_text = await response.text()
                            logger.error(f"Image API Error {response.status}: {error_text}")
                            if attempt == self.max_retries - 1:
                                return None
                            
            except asyncio.TimeoutError:
                logger.warning(f"Image generation timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Image generation error: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
        
        return None
    
    def _extract_image_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Извлечь изображение из ответа API.
        
        OpenRouter возвращает изображения в поле "images" сообщения:
        {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "...",
                    "images": [{
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,..."}
                    }]
                }
            }]
        }
        
        Args:
            response: Ответ от API.
            
        Returns:
            Optional[str]: Data URL изображения или None.
        """
        try:
            choices = response.get("choices", [])
            if not choices:
                logger.warning("No choices in response")
                return None
            
            message = choices[0].get("message", {})
            
            # Проверяем поле images (основной способ для OpenRouter)
            images = message.get("images", [])
            if images:
                for img in images:
                    if isinstance(img, dict):
                        image_url = img.get("image_url", {})
                        url = image_url.get("url", "")
                        if url.startswith("data:image"):
                            logger.info("Successfully extracted image from 'images' field")
                            return url
            
            content = message.get("content")
            
            # Проверяем, является ли content списком (multipart)
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        # Ищем image_url в части
                        if part.get("type") == "image_url":
                            image_url = part.get("image_url", {})
                            url = image_url.get("url", "")
                            if url.startswith("data:image"):
                                return url
                        # Или inline_data
                        elif "inline_data" in part:
                            inline = part["inline_data"]
                            mime = inline.get("mime_type", "image/png")
                            data = inline.get("data", "")
                            if data:
                                return f"data:{mime};base64,{data}"
            
            # Если content - строка, проверяем на base64
            elif isinstance(content, str):
                # Ищем base64 данные в тексте
                if "data:image" in content:
                    # Извлекаем data URL
                    match = re.search(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', content)
                    if match:
                        return match.group(0)
                
                # Проверяем, не является ли сам content base64
                if content.startswith("data:image"):
                    return content
            
            logger.warning(f"Could not extract image from response. Content type: {type(content)}, images field: {bool(images)}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting image from response: {str(e)}")
            return None


async def create_image_generator() -> ImageGenerator:
    """
    Фабричная функция для создания генератора изображений.
    
    Returns:
        ImageGenerator: Инициализированный генератор изображений.
        
    Raises:
        ValueError: Если отсутствует необходимая конфигурация.
    """
    if not Config.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in environment variables")
    
    return ImageGenerator(Config.OPENROUTER_API_KEY, Config.IMAGE_MODEL_NAME)
