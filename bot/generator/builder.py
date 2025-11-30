"""
Модуль строителя карточек для генерации карточек товаров.

Обрабатывает генерацию карточек товаров из извлеченной информации.
"""

import os
import logging
from typing import Optional
from datetime import datetime

from bot.ai.text_analyzer import ProductInfo
from bot.generator.templates import get_template
from bot.config import Config
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class CardBuilder:
    """
    Строитель для генерации карточек товаров.
    
    Оркестрирует процесс генерации карточек с использованием шаблонов.
    Следует паттерну Строитель и принципу единой ответственности.
    """
    
    def __init__(self, template_name: str = 'minimal'):
        """
        Инициализация строителя карточек.
        
        Args:
            template_name: Имя используемого шаблона.
        """
        self.template_name = template_name
        self.template = get_template(template_name)
    
    def build_card(
        self,
        product_info: ProductInfo,
        card_filename: Optional[str] = None,
        product_image_url: Optional[str] = None
    ) -> str:
        """
        Создать и сохранить изображение карточки товара.
        
        Args:
            product_info: Объект ProductInfo с деталями продукта.
            card_filename: Необязательное пользовательское имя файла (без расширения).
            product_image_url: URL изображения товара для добавления на карточку.
            
        Returns:
            str: Путь к сгенерированному файлу карточки.
        """
        # Использовать fallback для названия, если не указано
        product_name = product_info.name or "Товар"
        
        logger.info(f"Building card for product: {product_name}")
        
        # Подготовить путь к файлу
        if not card_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            card_filename = f"card_{timestamp}"
        
        card_path = os.path.join(Config.CARDS_DIR, f"{card_filename}.png")
        
        # Отрендерить карточку
        try:
            image_data = self.template.render(
                product_name=product_name,
                price=product_info.price or "Цена не указана",
                description=product_info.description or "",
                category=product_info.category or "Общая",
                color=product_info.color,
                size=product_info.size,
                features=product_info.other_features or {},
                product_image_url=product_image_url
            )
            
            # Сохранить изображение
            os.makedirs(Config.CARDS_DIR, exist_ok=True)
            
            with open(card_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Card generated successfully: {card_path}")
            return card_path
        
        except Exception as e:
            logger.error(f"Failed to generate card: {str(e)}")
            raise
    
    def change_template(self, template_name: str) -> None:
        """
        Изменить шаблон для этого строителя.
        
        Args:
            template_name: Имя нового шаблона.
            
        Raises:
            ValueError: Если имя шаблона неверно.
        """
        self.template_name = template_name
        self.template = get_template(template_name)
        logger.info(f"Template changed to: {template_name}")


def create_card_from_text(
    text: str,
    product_info: ProductInfo,
    template_name: str = 'minimal',
    product_image_url: Optional[str] = None
) -> str:
    """
    Создать карточку из текстовой информации о продукте.
    
    Вспомогательная функция для упрощенного создания карточек.
    
    Args:
        text: Оригинальное текстовое описание.
        product_info: Извлеченная информация о продукте.
        template_name: Шаблон для рендеринга.
        product_image_url: URL изображения товара (может быть сгенерировано AI).
        
    Returns:
        str: Путь к сгенерированной карточке.
    """
    builder = CardBuilder(template_name)
    
    # Использовать хеш текста для имени файла
    import hashlib
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    
    return builder.build_card(
        product_info, 
        f"card_{template_name}_{text_hash}",
        product_image_url=product_image_url
    )


def create_card_from_image(
    image_url: str,
    product_info: ProductInfo,
    template_name: str = 'minimal'
) -> str:
    """
    Создать карточку из информации о продукте, извлеченной из изображения.
    
    Вспомогательная функция для упрощенного создания карточек из изображений.
    
    Args:
        image_url: URL изображения товара.
        product_info: Извлеченная информация о продукте.
        template_name: Шаблон для рендеринга.
        
    Returns:
        str: Путь к сгенерированной карточке.
    """
    builder = CardBuilder(template_name)
    
    # Использовать хеш изображения для имени файла
    import hashlib
    url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
    
    return builder.build_card(product_info, f"card_img_{template_name}_{url_hash}", product_image_url=image_url)
