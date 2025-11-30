"""
Обработчик фотографий для бота.

Обрабатывает генерацию карточек товаров по анализу фотографий.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.states.product_states import ProductCardStates
from bot.ai.client import create_ai_client
from bot.ai.vision_analyzer import VisionAnalyzer
from bot.generator.builder import create_card_from_image
from bot.generator.templates import list_templates
from bot.utils.logger import get_logger
from bot.utils.constants import BotMessages, TemplateInfo

logger = get_logger(__name__)

router = Router()


def get_template_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Создать inline клавиатуру для выбора шаблона.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура выбора шаблона.
    """
    buttons = [
        [
            InlineKeyboardButton(text="📱 Минимал", callback_data="photo_template_minimal"),
            InlineKeyboardButton(text="🌙 Тёмный", callback_data="photo_template_dark"),
        ],
        [
            InlineKeyboardButton(text="🛒 Маркетплейс", callback_data="photo_template_marketplace"),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def extract_price_from_text(text: str) -> str | None:
    """
    Извлечь цену из текста (подписи к фото).
    
    Args:
        text: Текст для анализа.
        
    Returns:
        Цена как строка или None.
    """
    import re
    
    if not text:
        return None
    
    # Паттерны для поиска цены
    patterns = [
        # "1500₽", "1 500 ₽", "1500 рублей", "1500 руб", "1500р"
        r'(\d[\d\s]*(?:[.,]\d+)?)\s*(?:₽|руб\.?|рублей|рубля|р\.?|р\b)',
        # "цена 1500", "цена: 1500", "стоимость 1500"
        r'(?:цена|стоимость|price|cost)[:\s]*(\d[\d\s]*(?:[.,]\d+)?)',
        # Число в начале или конце текста
        r'(?:^|\s)(\d{2,}(?:[.,]\d+)?)\s*$',
        r'^(\d{2,}(?:[.,]\d+)?)(?:\s|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower().strip())
        if match:
            price = match.group(1).replace(' ', '')
            # Нормализуем цену
            price = price.replace(',', '.')
            try:
                # Проверяем что это число
                float(price)
                return f"{price} ₽"
            except ValueError:
                continue
    
    return None


def extract_product_info_from_text(text: str) -> dict:
    """
    Извлечь информацию о товаре из текста без использования AI.
    
    Args:
        text: Текст с информацией о товаре.
        
    Returns:
        Словарь с извлечённой информацией.
    """
    import re
    
    result = {
        'name': None,
        'price': None,
        'description': None,
        'category': None,
        'color': None,
        'size': None
    }
    
    if not text:
        return result
    
    text = text.strip()
    
    # Извлечь цену
    price = extract_price_from_text(text)
    if price:
        result['price'] = price
        # Удалить цену из текста для определения названия
        text_without_price = re.sub(r'\d[\d\s]*(?:[.,]\d+)?\s*(?:₽|руб\.?|рублей|рубля|р\.?|р\b)?', '', text, count=1).strip()
    else:
        text_without_price = text
    
    # Извлечь категорию (ищем "категория: xxx" или "категория - xxx" или "категория -xxx")
    category_match = re.search(r'категори[яю][:\s\-]+\s*([^,\n]+)', text_without_price, re.IGNORECASE)
    if category_match:
        result['category'] = category_match.group(1).strip().capitalize()
        text_without_price = re.sub(r'категори[яю][:\s\-]+\s*[^,\n]+[,]?\s*', '', text_without_price, flags=re.IGNORECASE).strip()
    
    # Извлечь размер
    size_patterns = [
        r'\b(размер\s*[:\-]?\s*\w+)',
        r'\b(xl|xxl|xxxl|xs|s|m|l)\b',
        r'\b(\d+\s*(?:см|мм|м|x|х)\s*\d*)',
        r'\b(большой|средний|маленький)\b'
    ]
    for pattern in size_patterns:
        match = re.search(pattern, text_without_price.lower())
        if match:
            result['size'] = match.group(1).strip()
            text_without_price = re.sub(pattern, '', text_without_price, flags=re.IGNORECASE).strip()
            break
    
    # Извлечь цвет
    colors = ['красный', 'синий', 'зелёный', 'зеленый', 'жёлтый', 'желтый', 'белый', 'чёрный', 'черный', 
              'розовый', 'оранжевый', 'фиолетовый', 'голубой', 'серый', 'коричневый', 'бежевый']
    for color in colors:
        if color in text_without_price.lower():
            result['color'] = color.capitalize()
            # Удаляем "цвет X" или просто название цвета из текста
            text_without_price = re.sub(rf'цвет\s+{color}', '', text_without_price, flags=re.IGNORECASE).strip()
            text_without_price = re.sub(rf'\b{color}\b', '', text_without_price, flags=re.IGNORECASE).strip()
            break
    
    # Оставшийся текст - это название/описание
    # Убираем лишние запятые и пробелы
    text_without_price = re.sub(r'\s*,\s*', ', ', text_without_price)
    text_without_price = re.sub(r'\s+', ' ', text_without_price).strip()
    text_without_price = text_without_price.strip(',').strip()
    
    if text_without_price:
        # Первая часть (до запятой) - название, остальное - описание
        parts = text_without_price.split(',', 1)
        result['name'] = parts[0].strip().capitalize()
        if len(parts) > 1:
            # Фильтруем описание от уже извлечённых полей
            desc = parts[1].strip()
            desc_parts = [p.strip() for p in desc.split(',') if p.strip() and 
                          not any(kw in p.lower() for kw in ['размер', 'категори', 'цвет', 'букет'])]
            if desc_parts:
                result['description'] = ', '.join(desc_parts)
    
    return result


@router.message(StateFilter(ProductCardStates.processing_image), F.photo)
async def process_product_photo(message: Message, state: FSMContext) -> None:
    """
    Обработка фотографии продукта для анализа.
    
    Args:
        message: Сообщение с фотографией.
        state: Контекст FSM.
    """
    # Показать индикатор загрузки
    loading_msg = await message.answer(BotMessages.PROCESSING_PHOTO)
    
    # Получить подпись к фото (caption) - там может быть цена
    caption = message.caption or ""
    caption_price = extract_price_from_text(caption)
    
    try:
        # Получить информацию о файле фотографии
        photo = message.photo[-1]  # Получить наивысшее качество
        file_info = await message.bot.get_file(photo.file_id)
        photo_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_info.file_path}"
        
        # Сохранить URL фотографии
        await state.update_data(photo_url=photo_url)
        
        # Создать AI клиент и анализатор изображений
        ai_client = await create_ai_client()
        vision_analyzer = VisionAnalyzer(ai_client)
        
        # Анализировать изображение
        product_info = await vision_analyzer.analyze_product_image(photo_url)
        
        # Если в подписи указана цена - она имеет приоритет
        if caption_price:
            product_info.price = caption_price
            logger.info(f"User {message.from_user.id}: Price from caption: {caption_price}")
        
        # Если в подписи есть другой текст - обработать как дополнительное описание
        if caption and not caption_price:
            # Анализируем текст подписи для извлечения информации
            from bot.ai.text_analyzer import TextAnalyzer
            text_analyzer = TextAnalyzer(ai_client)
            caption_info = await text_analyzer.extract_product_info(caption)
            
            # Объединяем: подпись имеет приоритет над AI-анализом фото
            if caption_info.name:
                product_info.name = caption_info.name
            if caption_info.price:
                product_info.price = caption_info.price
            if caption_info.description:
                if product_info.description:
                    product_info.description = f"{product_info.description}. {caption_info.description}"
                else:
                    product_info.description = caption_info.description
            if caption_info.category:
                product_info.category = caption_info.category
        
        # Сохранить информацию о продукте
        await state.update_data(product_info=product_info.to_dict())
        
        # Изменить сообщение о загрузке
        await loading_msg.delete()
        
        # Показать извлеченную информацию и предложить добавить описание
        price_note = ""
        if not product_info.price or product_info.price == "Не указана":
            price_note = "\n💡 **Совет:** Напишите цену (например: `1500` или `1500₽`)"
        
        confirmation_text = f"""
✅ **Информация о товаре из фото:**

📦 **Название:** {product_info.name or "Не определено"}
💰 **Цена:** {product_info.price or "Не указана"}
📂 **Категория:** {product_info.category or "Общая"}
🎨 **Цвет:** {product_info.color or "Не указан"}
📏 **Размер:** {product_info.size or "Не указан"}
📝 **Описание:** {product_info.description or "Не предоставлено"}
{price_note}
📝 **Введите текст, чтобы добавить/изменить цену или описание.**
Или нажмите "Продолжить", чтобы сразу перейти к выбору шаблона.
"""
        
        # Запросить подтверждение
        confirm_buttons = [
            [
                InlineKeyboardButton(text="✅ Продолжить", callback_data="photo_confirm_yes"),
            ],
        ]
        
        await message.answer(
            confirmation_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=confirm_buttons)
        )
        
        await state.set_state(ProductCardStates.confirming_extracted_data)
        logger.info(f"User {message.from_user.id}: Photo analyzed")
        
    except Exception as e:
        await loading_msg.delete()
        logger.error(f"Error processing photo: {str(e)}")
        await message.answer(
            f"❌ Error: {str(e)}\\n\\nPlease try again with a different photo."
        )
        await state.set_state(ProductCardStates.waiting_for_input)


@router.message(StateFilter(ProductCardStates.processing_image))
async def invalid_photo_handler(message: Message) -> None:
    """
    Обработка неверного ввода в режиме фото (не фотография).
    
    Args:
        message: Входящее сообщение.
    """
    await message.answer(BotMessages.ERROR_INVALID_PHOTO)
    logger.warning(f"User {message.from_user.id}: Sent non-photo in photo mode")


@router.callback_query(F.data == "photo_confirm_yes")
async def confirm_photo_info_handler(query, state: FSMContext) -> None:
    """
    Обработка подтверждения информации, извлеченной из фото.
    
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
    logger.info(f"User {query.from_user.id}: Confirmed photo info, selecting template")


@router.callback_query(F.data == "photo_confirm_no")
async def edit_photo_info_handler(query, state: FSMContext) -> None:
    """
    Обработка редактирования информации, извлеченной из фото.
    
    Args:
        query: Callback запрос.
        state: Контекст FSM.
    """
    await query.answer()
    
    await query.message.answer(
        "📝 Пожалуйста, предоставь исправленную информацию о товаре:"
    )
    
    await state.set_state(ProductCardStates.waiting_for_missing_info)
    logger.info(f"User {query.from_user.id}: Chose to edit photo-extracted info")


@router.message(StateFilter(ProductCardStates.confirming_extracted_data), F.text)
async def add_text_to_photo_handler(message: Message, state: FSMContext) -> None:
    """
    Обработка добавления текстового описания к информации из фото.
    
    Args:
        message: Сообщение с дополнительным текстом.
        state: Контекст FSM.
    """
    user_text = message.text
    
    # Получить сохраненную информацию о продукте
    data = await state.get_data()
    product_dict = data.get("product_info", {})
    
    # Извлечь информацию из текста локально (без AI)
    extracted = extract_product_info_from_text(user_text)
    
    # Применить извлечённые данные (текст пользователя имеет приоритет)
    if extracted['name']:
        product_dict['name'] = extracted['name']
    if extracted['price']:
        product_dict['price'] = extracted['price']
    if extracted['description']:
        current_desc = product_dict.get('description', '')
        if current_desc and current_desc != 'Не предоставлено':
            product_dict['description'] = f"{current_desc}. {extracted['description']}"
        else:
            product_dict['description'] = extracted['description']
    if extracted['category']:
        product_dict['category'] = extracted['category']
    if extracted['color']:
        product_dict['color'] = extracted['color']
    if extracted['size']:
        product_dict['size'] = extracted['size']
    
    logger.info(f"User {message.from_user.id}: Extracted from text: {extracted}")
    
    # Сохранить обновленную информацию
    await state.update_data(product_info=product_dict)
    
    # Показать обновленную информацию
    updated_text = f"""
✅ **Обновленная информация о товаре:**

📦 **Название:** {product_dict.get('name') or 'Не определено'}
💰 **Цена:** {product_dict.get('price') or 'Не указана'}
📂 **Категория:** {product_dict.get('category') or 'Общая'}
🎨 **Цвет:** {product_dict.get('color') or 'Не указан'}
📏 **Размер:** {product_dict.get('size') or 'Не указан'}
📝 **Описание:** {product_dict.get('description') or 'Не предоставлено'}

🎨 **Выберите шаблон для карточки:**
"""
    
    templates_info = list_templates()
    for template_name, info in templates_info.items():
        updated_text += f"\n**{info['name']}:** {info['description']}"
    
    await message.answer(
        updated_text,
        reply_markup=get_template_selection_keyboard()
    )
    
    await state.set_state(ProductCardStates.selecting_template)
    logger.info(f"User {message.from_user.id}: Added text description to photo info")


@router.callback_query(F.data.startswith("photo_template_"))
async def select_photo_template_handler(query, state: FSMContext) -> None:
    """
    Обработка выбора шаблона для карточки, сгенерированной по фото.
    
    Args:
        query: Callback запрос.
        state: Контекст FSM.
    """
    await query.answer("🎨 Генерирую карточку...")
    
    template_name = query.data.split("_")[2]  # Извлечь имя шаблона
    
    try:
        # Получить сохраненные данные
        data = await state.get_data()
        product_dict = data.get("product_info", {})
        photo_url = data.get("photo_url", "")
        
        # Создать объект информации о продукте
        from bot.ai.text_analyzer import ProductInfo
        product_info = ProductInfo(**product_dict)
        
        # Сгенерировать карточку
        card_path = create_card_from_image(photo_url, product_info, template_name)
        
        # Отправить карточку пользователю
        photo = FSInputFile(card_path)
        await query.message.answer_photo(
            photo=photo,
            caption=BotMessages.CARD_GENERATED.format(template=TemplateInfo.TEMPLATES[template_name]['name'])
        )
        
        logger.info(f"User {query.from_user.id}: Photo card generated with template {template_name}")
        
        # Запросить следующее действие
        from bot.handlers.menu import get_main_menu
        await query.message.answer(
            "Что ты хочешь сделать дальше?",
            reply_markup=get_main_menu()
        )
        
        await state.set_state(ProductCardStates.waiting_for_input)
        
    except Exception as e:
        logger.error(f"Error generating photo card: {str(e)}")
        await query.message.answer(
            f"❌ Error generating card: {str(e)}"
        )
