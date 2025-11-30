"""
Инициализация и реестр шаблонов.

Предоставляет фабрику и реестр для всех доступных шаблонов.
"""

from bot.generator.templates.base import BaseTemplate
from bot.generator.templates.minimal import MinimalTemplate
from bot.generator.templates.dark import DarkTemplate
from bot.generator.templates.marketplace import MarketplaceTemplate


# Реестр шаблонов
TEMPLATES = {
    'minimal': MinimalTemplate,
    'dark': DarkTemplate,
    'marketplace': MarketplaceTemplate,
}


def get_template(template_name: str) -> BaseTemplate:
    """
    Получить экземпляр шаблона по имени.
    
    Args:
        template_name: Имя шаблона ('minimal', 'dark', 'marketplace').
        
    Returns:
        BaseTemplate: Экземпляр шаблона.
        
    Raises:
        ValueError: Если имя шаблона не найдено.
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Template '{template_name}' not found. Available: {list(TEMPLATES.keys())}")
    
    return TEMPLATES[template_name]()


def list_templates() -> dict:
    """
    Получить информацию о всех доступных шаблонах.
    
    Returns:
        dict: Словарь с информацией о шаблонах.
    """
    templates_info = {}
    for name, template_class in TEMPLATES.items():
        template = template_class()
        templates_info[name] = {
            'name': template.get_template_name(),
            'description': template.get_description(),
        }
    
    return templates_info
