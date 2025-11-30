"""
Обработчики текстовых описаний для бота.

Обрабатывает генерацию карточек товаров из текстовых описаний.
"""

import re
import json
import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.states.product_states import ProductCardStates
from bot.ai.client import create_ai_client
from bot.ai.text_analyzer import TextAnalyzer, ProductInfo
from bot.ai.image_generator import create_image_generator
from bot.generator.builder import create_card_from_text
from bot.generator.templates import list_templates
from bot.utils.logger import get_logger
from bot.utils.constants import BotMessages, TemplateInfo

logger = get_logger(__name__)

router = Router()


def extract_price_from_text(text: str) -> str | None:
    """
    Извлечь цену из текста.
    
    Args:
        text: Текст для анализа.
        
    Returns:
        Цена как строка или None.
    """
    if not text:
        return None
    
    # Ищем числа рядом с символами валюты или просто числа
    patterns = [
        r'(\d[\d\s]*(?:[.,]\d+)?)\s*(?:₽|руб\.?|рублей|рубля)',
        r'(?:цена|стоимость)[:\s]*(\d[\d\s]*(?:[.,]\d+)?)',
        r'(?:^|,\s*)(\d{3,})\s*(?:,|$)',  # число от 3 цифр между запятыми
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                price = match.group(1).replace(' ', '').replace(',', '.')
                float(price)
                return f"{price} ₽"
            except (ValueError, IndexError):
                continue
    
    # Fallback: ищем любое число от 3 цифр
    numbers = re.findall(r'\b(\d{3,})\b', text)
    if numbers:
        return f"{numbers[0]} ₽"
    
    return None


def extract_product_info_locally(text: str) -> ProductInfo:
    """
    Извлечь информацию о товаре из текста локально (без AI).
    
    Args:
        text: Текст с информацией о товаре.
        
    Returns:
        ProductInfo с извлечённой информацией.
    """
    result = {
        'name': None,
        'price': None,
        'description': None,
        'category': None,
        'color': None,
        'size': None
    }
    
    if not text:
        return ProductInfo(**result)
    
    text = text.strip()
    working_text = text
    
    # Извлечь цену
    price = extract_price_from_text(text)
    if price:
        result['price'] = price
        # Удалить цену из текста
        working_text = re.sub(r'\d[\d\s]*(?:[.,]\d+)?\s*(?:₽|руб\.?|рублей|рубля|р\.?|р\b)?', '', working_text, count=1).strip()
    
    # Извлечь категорию (ищем "категория: xxx" или "категория - xxx" или "категория -xxx")
    category_match = re.search(r'категори[яю][:\s\-]+\s*([^,\n]+)', working_text, re.IGNORECASE)
    if category_match:
        result['category'] = category_match.group(1).strip().capitalize()
        working_text = re.sub(r'категори[яю][:\s\-]+\s*[^,\n]+[,]?\s*', '', working_text, flags=re.IGNORECASE).strip()
    
    # Извлечь размер
    size_patterns = [
        r'размер[:\s\-]+([^,\n]+)',
        r'\b(xl|xxl|xxxl|xs|s|m|l)\b',
        r'\b(\d+\s*(?:см|мм|м|x|х)\s*\d*)',
        r'\b(большой|средний|маленький|огромный|мини)\b'
    ]
    for pattern in size_patterns:
        match = re.search(pattern, working_text, re.IGNORECASE)
        if match:
            result['size'] = match.group(1).strip()
            working_text = re.sub(pattern, '', working_text, count=1, flags=re.IGNORECASE).strip()
            break
    
    # Извлечь цвет
    colors = {
        'красный': 'Красный', 'красная': 'Красный', 'красное': 'Красный',
        'синий': 'Синий', 'синяя': 'Синий', 'синее': 'Синий',
        'зелёный': 'Зелёный', 'зеленый': 'Зелёный', 'зелёная': 'Зелёный', 'зеленая': 'Зелёный',
        'жёлтый': 'Жёлтый', 'желтый': 'Жёлтый',
        'белый': 'Белый', 'белая': 'Белый', 'белое': 'Белый',
        'чёрный': 'Чёрный', 'черный': 'Чёрный', 'чёрная': 'Чёрный', 'черная': 'Чёрный',
        'розовый': 'Розовый', 'розовая': 'Розовый',
        'оранжевый': 'Оранжевый', 'оранжевая': 'Оранжевый',
        'фиолетовый': 'Фиолетовый', 'фиолетовая': 'Фиолетовый',
        'голубой': 'Голубой', 'голубая': 'Голубой',
        'серый': 'Серый', 'серая': 'Серый',
        'коричневый': 'Коричневый', 'коричневая': 'Коричневый',
        'бежевый': 'Бежевый', 'бежевая': 'Бежевый'
    }
    for color_word, color_name in colors.items():
        if color_word in working_text.lower():
            result['color'] = color_name
            # Удаляем "цвет X" или просто название цвета из текста
            working_text = re.sub(rf'цвет\s+{color_word}', '', working_text, flags=re.IGNORECASE).strip()
            working_text = re.sub(rf'\b{color_word}\b', '', working_text, flags=re.IGNORECASE).strip()
            break
    
    # Убираем лишние запятые и пробелы
    working_text = re.sub(r'\s*,\s*', ', ', working_text)
    working_text = re.sub(r'\s+', ' ', working_text).strip()
    working_text = working_text.strip(',').strip()
    
    if working_text:
        # Разделяем по запятой - первая часть название, остальное описание
        parts = [p.strip() for p in working_text.split(',') if p.strip()]
        if parts:
            result['name'] = parts[0].capitalize()
            if len(parts) > 1:
                # Собираем остальные части как описание (исключая уже извлечённое)
                desc_parts = [p for p in parts[1:] if p and 
                              not any(kw in p.lower() for kw in ['размер', 'категори', 'цвет', 'букет'])]
                if desc_parts:
                    result['description'] = ', '.join(desc_parts)
    
    return ProductInfo(**result)


def get_template_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Создать inline клавиатуру для выбора шаблона.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура выбора шаблона.
    """
    buttons = [
        [
            InlineKeyboardButton(text="📱 Минимал", callback_data="template_minimal"),
            InlineKeyboardButton(text="🌙 Тёмный", callback_data="template_dark"),
        ],
        [
            InlineKeyboardButton(text="🛒 Маркетплейс", callback_data="template_marketplace"),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(StateFilter(ProductCardStates.processing_text))
async def process_text_description(message: Message, state: FSMContext) -> None:
    """
    Обработка текстового описания продукта.
    
    Args:
        message: Входящее сообщение с описанием продукта.
        state: Контекст FSM.
    """
    user_text = message.text
    
    # Сохранить оригинальный текст
    await state.update_data(original_text=user_text)
    
    # Показать индикатор загрузки
    loading_msg = await message.answer(BotMessages.PROCESSING_TEXT)
    
    try:
        # Сначала пробуем локальный парсинг (быстро и надёжно)
        product_info = extract_product_info_locally(user_text)
        
        # Если локальный парсинг не извлёк название, пробуем AI
        if not product_info.name:
            try:
                ai_client = await create_ai_client()
                text_analyzer = TextAnalyzer(ai_client)
                product_info = await text_analyzer.extract_product_info(user_text)
            except Exception as ai_error:
                logger.warning(f"AI extraction failed, using local: {ai_error}")
                # Если AI не сработал, используем весь текст как название
                product_info = ProductInfo(
                    name=user_text[:50] + "..." if len(user_text) > 50 else user_text,
                    price=extract_price_from_text(user_text)
                )
        
        # Сохранить информацию о продукте
        await state.update_data(product_info=product_info.to_dict())
        
        # Изменить сообщение о загрузке
        await loading_msg.delete()
        
        # Показать извлеченную информацию для подтверждения
        confirmation_text = f"""
✅ **Извлечённая информация о товаре:**

📦 **Название:** {product_info.name or "Не определено"}
💰 **Цена:** {product_info.price or "Не указана"}
📂 **Категория:** {product_info.category or "Общая"}
🎨 **Цвет:** {product_info.color or "Не указан"}
📏 **Размер:** {product_info.size or "Не указан"}
📝 **Описание:** {product_info.description or "Не предоставлено"}

Всё верно?
"""
        
        # Запросить подтверждение
        confirm_buttons = [
            [
                InlineKeyboardButton(text="✅ Да, продолжить", callback_data="confirm_info_yes"),
                InlineKeyboardButton(text="❌ Нет, исправить", callback_data="confirm_info_no"),
            ],
        ]
        
        await message.answer(
            confirmation_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=confirm_buttons)
        )
        
        await state.set_state(ProductCardStates.confirming_extracted_data)
        logger.info(f"User {message.from_user.id}: Product info extracted - {product_info.name}")
        
    except Exception as e:
        await loading_msg.delete()
        logger.error(f"Error processing text: {str(e)}")
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте ещё раз с другим описанием."
        )
        await state.set_state(ProductCardStates.waiting_for_input)


@router.callback_query(F.data == "confirm_info_yes")
async def confirm_info_handler(query, state: FSMContext) -> None:
    """
    Обработка подтверждения извлеченной информации о продукте.
    
    Args:
        query: Callback запрос.
        state: Контекст FSM.
    """
    await query.answer()
    
    # Перейти к выбору шаблона
    templates_text = "🎨 **Выбери шаблон для карточки:**\n\n"
    
    templates_info = list_templates()
    for template_name, info in templates_info.items():
        templates_text += f"**{info['name']}:** {info['description']}\n\n"
    
    await query.message.answer(
        templates_text,
        reply_markup=get_template_selection_keyboard()
    )
    
    await state.set_state(ProductCardStates.selecting_template)
    logger.info(f"User {query.from_user.id}: Confirmed product info, selecting template")


@router.callback_query(F.data == "confirm_info_no")
async def edit_info_handler(query, state: FSMContext) -> None:
    """
    Обработка редактирования информации о продукте.
    
    Args:
        query: Callback запрос.
        state: Контекст FSM.
    """
    await query.answer()
    
    await query.message.answer(
        "📝 Пожалуйста, предоставь исправленную информацию о товаре:"
    )
    
    await state.set_state(ProductCardStates.waiting_for_missing_info)
    logger.info(f"User {query.from_user.id}: Chose to edit product info")


@router.callback_query(F.data.startswith("template_"))
async def select_template_handler(query, state: FSMContext) -> None:
    """
    Обработка выбора шаблона.
    
    Args:
        query: Callback запрос.
        state: Контекст FSM.
    """
    await query.answer("🎨 Генерирую карточку...")
    
    template_name = query.data.split("_")[1]  # Извлечь имя шаблона
    
    try:
        # Получить сохраненную информацию о продукте
        data = await state.get_data()
        product_dict = data.get("product_info", {})
        original_text = data.get("original_text", "")
        
        # Создать объект информации о продукте
        from bot.ai.text_analyzer import ProductInfo
        product_info = ProductInfo(**product_dict)
        
        # Генерируем AI изображение товара
        product_image_url = None
        try:
            # Показываем статус генерации
            status_msg = await query.message.answer("🖼️ Генерирую изображение товара...")
            
            image_generator = await create_image_generator()
            product_image_url = await image_generator.generate_product_image(
                product_name=product_info.name or "товар",
                category=product_info.category,
                color=product_info.color,
                size=product_info.size
            )
            
            await status_msg.delete()
            
            if product_image_url:
                logger.info(f"AI image generated for product: {product_info.name}")
            else:
                logger.warning(f"AI image generation returned None for: {product_info.name}")
                
        except Exception as img_error:
            logger.warning(f"Image generation failed: {img_error}")
            # Продолжаем без изображения
        
        # Сгенерировать карточку
        card_path = create_card_from_text(
            original_text, 
            product_info, 
            template_name,
            product_image_url=product_image_url
        )
        
        # Отправить карточку пользователю
        photo = FSInputFile(card_path)
        await query.message.answer_photo(
            photo=photo,
            caption=BotMessages.CARD_GENERATED.format(template=TemplateInfo.TEMPLATES[template_name]['name'])
        )
        
        logger.info(f"User {query.from_user.id}: Card generated with template {template_name}")
        
        # Запросить следующее действие
        from bot.handlers.menu import get_main_menu
        await query.message.answer(
            "Что ты хочешь сделать дальше?",
            reply_markup=get_main_menu()
        )
        
        await state.set_state(ProductCardStates.waiting_for_input)
        
    except Exception as e:
        logger.error(f"Error generating card: {str(e)}")
        await query.message.answer(
            f"❌ Error generating card: {str(e)}"
        )


@router.message(StateFilter(ProductCardStates.waiting_for_missing_info))
async def process_missing_info(message: Message, state: FSMContext) -> None:
    """
    Обработка исправленной/отсутствующей информации о продукте.
    
    Args:
        message: Сообщение с исправленной информацией.
        state: Контекст FSM.
    """
    # Повторно обработать с обновленной информацией
    await process_text_description(message, state)
