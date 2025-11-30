"""
Тёмный шаблон для карточек товаров.

Современный тёмный дизайн для карточек товаров.
"""

from typing import Optional, Dict
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from bot.generator.templates.base import BaseTemplate, TemplateConfig
from bot.generator.templates.minimal import download_image_sync


class DarkTemplate(BaseTemplate):
    """
    Тёмный шаблон карточки товара.
    
    Тёмный фон с яркими акцентами.
    Идеально для премиум и люксовых товаров.
    """
    
    @staticmethod
    def get_default_config() -> TemplateConfig:
        """
        Получить конфигурацию по умолчанию для тёмного шаблона.
        
        Returns:
            TemplateConfig: Конфигурация шаблона по умолчанию.
        """
        return TemplateConfig(
            width=800,
            height=800,
            background_color=(20, 20, 30),  # Dark blue-black
            text_color=(240, 240, 240),  # Light gray
            accent_color=(255, 100, 100),  # Red-pink
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
        Отрендерить тёмную карточку товара.
        
        Args:
            product_name: Название товара.
            price: Цена товара.
            description: Описание товара.
            category: Категория товара.
            color: Цвет товара.
            size: Размер товара.
            features: Дополнительные характеристики.
            product_image_url: URL изображения товара.
            
        Returns:
            bytes: PNG данные изображения.
        """
        # Create image with dark background
        img = Image.new(
            'RGB',
            (self.config.width, self.config.height),
            self.config.background_color
        )
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype(self.config.font_name, self.config.title_font_size)
            body_font = ImageFont.truetype(self.config.font_name, self.config.body_font_size)
            price_font = ImageFont.truetype(self.config.font_name, self.config.price_font_size)
        except IOError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
        
        # Draw accent line at top
        draw.rectangle(
            [(0, 0), (self.config.width, 5)],
            fill=self.config.accent_color
        )
        
        # Load and paste product image
        image_height = 350
        if product_image_url:
            product_img = download_image_sync(product_image_url)
            if product_img:
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
                
                if product_img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', product_img.size, self.config.background_color)
                    if product_img.mode == 'P':
                        product_img = product_img.convert('RGBA')
                    background.paste(product_img, mask=product_img.split()[-1] if product_img.mode == 'RGBA' else None)
                    product_img = background
                
                x_pos = (self.config.width - new_width) // 2
                y_pos = 20
                img.paste(product_img, (x_pos, y_pos))
        
        # Draw category with accent
        y_offset = image_height + 40
        draw.text(
            (40, y_offset),
            f"◆ {category.upper()}",
            fill=self.config.accent_color,
            font=body_font
        )
        
        # Draw title - with word wrap for long names
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
        
        # Draw description
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
        
        # Draw size if provided
        if size:
            y_offset += 10
            draw.text(
                (40, y_offset),
                f"Размер: {size}",
                fill=self.config.text_color,
                font=body_font
            )
        
        # Draw price with styling
        price_y = self.config.height - 80
        price_text = price if price else "Цена не указана"
        draw.text(
            (40, price_y),
            price_text,
            fill=self.config.accent_color,
            font=price_font
        )
        
        # Draw footer accent line
        draw.rectangle(
            [(0, self.config.height - 5), (self.config.width, self.config.height)],
            fill=self.config.accent_color
        )
        
        # Save to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    def get_template_name(self) -> str:
        """Получить название шаблона."""
        return "dark"
    
    @staticmethod
    def get_description() -> str:
        """Получить описание шаблона."""
        return "Тёмный, роскошный дизайн с яркими акцентами. Идеально для премиум товаров."
    
    @staticmethod
    def _wrap_text(text: str, max_width: int) -> list:
        """
        Перенос текста по ширине.
        
        Args:
            text: Текст для переноса.
            max_width: Максимальное количество символов в строке.
            
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
