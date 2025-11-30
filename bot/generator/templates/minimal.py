"""
Минималистичный шаблон для карточек товаров.

Чистый, минималистичный дизайн шаблона для карточек товаров.
"""

from typing import Optional, Dict
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp
import asyncio
import base64
import re

from bot.generator.templates.base import BaseTemplate, TemplateConfig


def download_image_sync(url: str) -> Optional[Image.Image]:
    """
    Синхронно загрузить изображение по URL или из base64 data URL.
    
    Args:
        url: URL изображения или data URL (base64).
        
    Returns:
        Image.Image или None при ошибке.
    """
    try:
        # Проверяем, является ли это data URL (base64)
        if url.startswith("data:image"):
            # Извлекаем base64 данные
            match = re.match(r'data:image/[^;]+;base64,(.+)', url)
            if match:
                base64_data = match.group(1)
                image_data = base64.b64decode(base64_data)
                return Image.open(BytesIO(image_data))
        else:
            # Обычный URL - загружаем через requests
            import requests
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
    except Exception as e:
        import logging
        logging.error(f"Error loading image: {e}")
    return None


class MinimalTemplate(BaseTemplate):
    """
    Минималистичный шаблон карточки товара.
    
    Отличается чистым, современным дизайном с большим количеством свободного пространства.
    Подходит для товаров, которые должны говорить сами за себя.
    """
    
    @staticmethod
    def get_default_config() -> TemplateConfig:
        """
        Получить конфигурацию по умолчанию для минималистичного шаблона.
        
        Returns:
            TemplateConfig: Конфигурация шаблона по умолчанию.
        """
        return TemplateConfig(
            width=800,
            height=800,
            background_color=(255, 255, 255),  # Белый
            text_color=(40, 40, 40),  # Темно-серый
            accent_color=(0, 122, 255),  # Синий
            font_name="arial.ttf",
            title_font_size=36,
            body_font_size=18,
            price_font_size=42
        )
    
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
        Отрендерить минималистичную карточку товара.
        
        Args:
            product_name: Название продукта.
            price: Цена продукта.
            description: Описание продукта.
            category: Категория продукта.
            color: Цвет продукта.
            size: Размер продукта.
            features: Дополнительные характеристики.
            product_image_url: URL изображения товара.
            
        Returns:
            bytes: Данные PNG изображения.
        """
        # Создать изображение
        img = Image.new(
            'RGB',
            (self.config.width, self.config.height),
            self.config.background_color
        )
        draw = ImageDraw.Draw(img)
        
        # Попытаться загрузить шрифты
        try:
            title_font = ImageFont.truetype(self.config.font_name, self.config.title_font_size)
            body_font = ImageFont.truetype(self.config.font_name, self.config.body_font_size)
            price_font = ImageFont.truetype(self.config.font_name, self.config.price_font_size)
        except IOError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
        
        # Загрузить и вставить изображение товара
        image_height = 350
        if product_image_url:
            product_img = download_image_sync(product_image_url)
            if product_img:
                # Масштабировать изображение
                img_ratio = product_img.width / product_img.height
                target_width = self.config.width - 80
                target_height = image_height
                
                if img_ratio > target_width / target_height:
                    new_width = target_width
                    new_height = int(target_width / img_ratio)
                else:
                    new_height = target_height
                    new_width = int(target_height * img_ratio)
                
                product_img = product_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Конвертировать в RGB если нужно
                if product_img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', product_img.size, self.config.background_color)
                    if product_img.mode == 'P':
                        product_img = product_img.convert('RGBA')
                    background.paste(product_img, mask=product_img.split()[-1] if product_img.mode == 'RGBA' else None)
                    product_img = background
                
                # Центрировать изображение
                x_pos = (self.config.width - new_width) // 2
                y_pos = 20
                img.paste(product_img, (x_pos, y_pos))
        
        # Нарисовать категорию
        y_offset = image_height + 40
        draw.text(
            (40, y_offset),
            category.upper(),
            fill=self.config.accent_color,
            font=body_font
        )
        
        # Нарисовать заголовок (название продукта) - с переносом для длинных названий
        y_offset += 35
        title_lines = self._wrap_text(product_name, 40)
        for line in title_lines[:2]:  # Максимум 2 строки
            draw.text(
                (40, y_offset),
                line,
                fill=self.config.text_color,
                font=title_font
            )
            y_offset += 42
        
        # Нарисовать описание
        y_offset += 8
        if description:
            for line in self._wrap_text(description, 55):
                draw.text(
                    (40, y_offset),
                    line,
                    fill=self.config.text_color,
                    font=body_font
                )
                y_offset += 28
        
        # Нарисовать размер если есть
        if size:
            y_offset += 10
            draw.text(
                (40, y_offset),
                f"Размер: {size}",
                fill=self.config.text_color,
                font=body_font
            )
        
        # Нарисовать блок цены внизу
        box_y = self.config.height - 80
        draw.rectangle(
            [(0, box_y), (self.config.width, self.config.height)],
            fill=self.config.accent_color
        )
        
        # Отобразить цену
        price_text = price if price else "Цена не указана"
        draw.text(
            (40, box_y + 18),
            price_text,
            fill=(255, 255, 255),
            font=price_font
        )
        
        # Сохранить в байты
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    def get_template_name(self) -> str:
        """Получить имя шаблона."""
        return "minimal"
    
    @staticmethod
    def get_description() -> str:
        """Получить описание шаблона."""
        return "Чистый, минималистичный дизайн с большим количеством пространства. Идеально для современных товаров."
    
    @staticmethod
    def _wrap_text(text: str, max_width: int) -> list:
        """
        Перенос текста для соответствия максимальной ширине.
        
        Args:
            text: Текст для переноса.
            max_width: Максимальное количество символов на строку.
            
        Returns:
            list: Список строк текста.
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > max_width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
