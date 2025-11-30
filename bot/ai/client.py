"""
Модуль AI клиента для интеграции с OpenRouter API.

Предоставляет абстрактный слой для взаимодействия с OpenRouter API и различными AI моделями.
"""

import logging
from typing import Any, Dict, List, Optional
import aiohttp
import asyncio

from bot.config import Config
from bot.utils.logger import get_logger
from bot.utils.constants import AIConfig

logger = get_logger(__name__)


class OpenRouterClient:
    """
    Клиент для взаимодействия с OpenRouter API.
    
    Обрабатывает API запросы, ограничение скорости и обработку ошибок для взаимодействия с AI моделями.
    Следует принципу SOLID единой ответственности.
    """
    
    def __init__(self, api_key: str, model_name: str):
        """
        Инициализация OpenRouter клиента.
        
        Args:
            api_key: Ключ OpenRouter API.
            model_name: Используемая AI модель (например, 'google/gemini-2.0-flash-thinking-exp-1219').
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://openrouter.io/api/v1"
        self.max_retries = 3
        self.retry_delay = 2  # секунды
    
    async def _make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Выполнить HTTP запрос к OpenRouter API с логикой повторных попыток.
        
        Args:
            endpoint: Конечная точка API (например, '/chat/completions').
            method: HTTP метод ('POST' или 'GET').
            data: Полезная нагрузка запроса.
            timeout: Таймаут запроса в секундах.
            
        Returns:
            Dict[str, Any]: Ответ API в виде словаря.
            
        Raises:
            Exception: Если запрос API не удался после всех попыток.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Jeff555max/Product_card_generator",
            "X-Title": "Product Card Generator",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        json=data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Ограничение скорости
                            wait_time = self.retry_delay * (2 ** attempt)
                            logger.warning(
                                f"Rate limited. Waiting {wait_time}s before retry (attempt {attempt + 1}/{self.max_retries})"
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            error_text = await response.text()
                            logger.error(f"API Error {response.status}: {error_text}")
                            raise Exception(f"API request failed with status {response.status}")
            
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay)
        
        raise Exception("API request failed after all retries")
    
    async def analyze_text(self, text: str, prompt: str) -> str:
        """
        Анализ текста с использованием AI модели и пользовательского промпта.
        
        Args:
            text: Текст для анализа.
            prompt: Системный промпт для анализа.
            
        Returns:
            str: Ответ анализа AI модели.
        """
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": AIConfig.TEMPERATURE_TEXT_EXTRACTION,
            "max_tokens": AIConfig.MAX_TOKENS_TEXT_EXTRACTION
        }
        
        try:
            response = await self._make_request("/chat/completions", data=payload)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Text analysis failed: {str(e)}")
            raise
    
    async def analyze_image(self, image_url: str, prompt: str) -> str:
        """
        Анализ изображения с использованием возможностей компьютерного зрения и пользовательского промпта.
        
        Args:
            image_url: URL изображения для анализа.
            prompt: Системный промпт для анализа.
            
        Returns:
            str: Анализ изображения AI моделью.
        """
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "temperature": AIConfig.TEMPERATURE_IMAGE_ANALYSIS,
            "max_tokens": AIConfig.MAX_TOKENS_IMAGE_ANALYSIS
        }
        
        try:
            response = await self._make_request("/chat/completions", data=payload)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            raise
    
    async def generate_completion(
        self, 
        prompt: str, 
        temperature: float = None, 
        max_tokens: int = None
    ) -> str:
        """
        Генерация завершения на основе промпта.
        
        Args:
            prompt: Промпт для AI.
            temperature: Температура выборки (0.0 до 1.0). Использует AIConfig.TEMPERATURE_DEFAULT если None.
            max_tokens: Максимальное количество токенов в ответе. Использует AIConfig.MAX_TOKENS_DEFAULT если None.
            
        Returns:
            str: Ответ AI.
        """
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature if temperature is not None else AIConfig.TEMPERATURE_DEFAULT,
            "max_tokens": max_tokens if max_tokens is not None else AIConfig.MAX_TOKENS_DEFAULT
        }
        
        try:
            response = await self._make_request("/chat/completions", data=payload)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Completion generation failed: {str(e)}")
            raise


async def create_ai_client() -> OpenRouterClient:
    """
    Фабричная функция для создания и инициализации OpenRouter клиента.
    
    Returns:
        OpenRouterClient: Инициализированный AI клиент.
        
    Raises:
        ValueError: Если отсутствует необходимая конфигурация.
    """
    if not Config.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set in environment variables")
    
    return OpenRouterClient(Config.OPENROUTER_API_KEY, Config.MODEL_NAME)
