"""
Базовый шаблон для карточек товаров.

Предоставляет абстрактный базовый класс для шаблонов карточек.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class TemplateConfig:
    """Конфигурация для рендеринга шаблона."""
    width: int
    height: int
    background_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    font_name: str
    title_font_size: int
    body_font_size: int
    price_font_size: int


class BaseTemplate(ABC):
    """
    Абстрактный базовый класс для шаблонов карточек товаров.
    
    Определяет интерфейс, которому должны следовать все реализации шаблонов.
    Следует принципу открытости/закрытости (OCP) - открыт для расширения, закрыт для модификации.
    """
    
    def __init__(self, config: Optional[TemplateConfig] = None):
        """
        Инициализация шаблона.
        
        Args:
            config: Конфигурация шаблона. Использует значение по умолчанию, если None.
        """
        self.config = config or self.get_default_config()
    
    @staticmethod
    @abstractmethod
    def get_default_config() -> TemplateConfig:
        """
        Получить конфигурацию по умолчанию для этого шаблона.
        
        Returns:
            TemplateConfig: Конфигурация шаблона по умолчанию.
        """
        pass
    
    @abstractmethod
    def render(
        self,
        product_name: str,
        price: str,
        description: str,
        category: str,
        color: Optional[str] = None,
        size: Optional[str] = None,
        features: Optional[Dict[str, str]] = None,
        product_image_url: Optional[str] = None
    ) -> bytes:
        """
        Отрендерить карточку товара в виде PNG изображения.
        
        Args:
            product_name: Название продукта.
            price: Цена продукта.
            description: Описание продукта.
            category: Категория продукта.
            color: Цвет продукта.
            size: Размер продукта.
            features: Дополнительные характеристики продукта.
            product_image_url: URL изображения товара.
            
        Returns:
            bytes: Данные PNG изображения.
        """
        pass
    
    @abstractmethod
    def get_template_name(self) -> str:
        """
        Получить имя этого шаблона.
        
        Returns:
            str: Имя шаблона (например, 'minimal', 'dark').
        """
        pass
    
    @staticmethod
    @abstractmethod
    def get_description() -> str:
        """
        Получить читаемое описание этого шаблона.
        
        Returns:
            str: Описание шаблона.
        """
        pass
