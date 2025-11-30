# 🎨 Product Card Generator Bot

> **Telegram-бот с AI для автоматического создания профессиональных карточек товаров**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![aiogram](https://img.shields.io/badge/aiogram-3.0+-blue.svg)](https://docs.aiogram.dev/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-orange.svg)](https://openrouter.ai/)

---

## 📋 О проекте

Telegram-бот с искусственным интеллектом, который автоматически генерирует красивые карточки товаров. Бот может:
- **Анализировать текстовые описания** и извлекать информацию о товаре
- **Распознавать товары на фотографиях** с помощью AI Vision
- **Генерировать AI-изображения товаров** на основе текстового описания
- **Создавать готовые карточки** в нескольких стильных шаблонах

### ✨ Ключевые возможности

| Функция | Описание |
|---------|----------|
| 🤖 **AI-анализ текста** | Извлечение названия, цены, категории, размера из описания |
| 📸 **AI Vision** | Анализ фотографий товаров через Google Gemini 2.5 Flash |
| 🖼️ **AI-генерация изображений** | Создание изображений товаров через Gemini 2.5 Flash Image |
| 🎨 **3 шаблона** | Минимал, Тёмный, Маркетплейс |

---

## 🖼️ Примеры карточек

<table>
  <tr>
    <td align="center"><b>📱 Минимал</b></td>
    <td align="center"><b>🌙 Тёмный</b></td>
    <td align="center"><b>🛒 Маркетплейс</b></td>
  </tr>
  <tr>
    <td>Чистый современный дизайн</td>
    <td>Премиум-стиль с тёмным фоном</td>
    <td>Стиль e-commerce платформ</td>
  </tr>
</table>

---

## 🚀 Быстрый старт

### Требования

- Python 3.11+
- Telegram Bot Token ([получить у @BotFather](https://t.me/BotFather))
- OpenRouter API Key ([получить на openrouter.ai](https://openrouter.ai))

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Jeff555max/Product_card_generator.git
cd Product_card_generator

# 2. Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Отредактировать .env и добавить токены
```

### Конфигурация `.env`

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# OpenRouter API
OPENROUTER_API_KEY=your_api_key_here
MODEL_NAME=google/gemini-2.5-flash
IMAGE_MODEL_NAME=google/gemini-2.5-flash-image

# Settings
LOG_LEVEL=INFO
DEBUG=False
```

### Запуск

```bash
python -m bot.main
```

---

## 📖 Как пользоваться

### Из текста
1. `/start` → **"📝 Создать из текста"**
2. Отправьте описание:
   ```
   Беспроводные наушники Sony, цена 15990, категория электроника
   ```
3. Подтвердите данные → Выберите шаблон → Готово! 🎉

### Из фото
1. `/start` → **"📸 Создать из фото"**
2. Отправьте фото товара (можно с ценой в подписи)
3. AI проанализирует изображение
4. Подтвердите данные → Выберите шаблон → Готово! 🎉

---

## 🏗️ Структура проекта

```
Product_card_generator/
├── bot/
│   ├── ai/                     # AI-модули
│   │   ├── client.py           # OpenRouter API клиент
│   │   ├── image_generator.py  # Генерация изображений AI
│   │   ├── text_analyzer.py    # Анализ текста
│   │   └── vision_analyzer.py  # Анализ изображений
│   ├── generator/              # Генерация карточек
│   │   ├── builder.py          # Сборщик карточек
│   │   └── templates/          # Шаблоны
│   │       ├── minimal.py
│   │       ├── dark.py
│   │       └── marketplace.py
│   ├── handlers/               # Обработчики команд
│   │   ├── menu.py
│   │   ├── description.py
│   │   └── photo.py
│   ├── states/                 # FSM состояния
│   ├── utils/                  # Утилиты
│   ├── config.py               # Конфигурация
│   └── main.py                 # Точка входа
├── generated_cards/            # Сгенерированные карточки
├── .env                        # Переменные окружения
├── requirements.txt            # Зависимости
└── README.md
```

---

## 🛠️ Технологии

| Технология | Назначение |
|------------|------------|
| **[aiogram 3.0+](https://docs.aiogram.dev/)** | Асинхронный Telegram Bot API |
| **[OpenRouter](https://openrouter.ai/)** | Унифицированный доступ к AI моделям |
| **[Gemini 2.5 Flash](https://openrouter.ai/google/gemini-2.5-flash)** | Анализ текста и изображений |
| **[Gemini 2.5 Flash Image](https://openrouter.ai/google/gemini-2.5-flash-image)** | Генерация изображений (Nano Banana) |
| **[Pillow](https://pillow.readthedocs.io/)** | Обработка изображений |
| **[aiohttp](https://docs.aiohttp.org/)** | Асинхронные HTTP запросы |

---

## 📊 Архитектура

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Telegram      │────▶│   aiogram Bot    │────▶│   OpenRouter    │
│   User Input    │     │   (Handlers)     │     │   API           │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                                ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │   Card Builder   │◀────│   Gemini 2.5    │
                        │   (Templates)    │     │   Flash/Image   │
                        └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │   PNG Card       │
                        │   800x800px      │
                        └──────────────────┘
```

---

## 🔧 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запустить бота |
| `/help` | Показать справку |
| `/cancel` | Отменить операцию |













