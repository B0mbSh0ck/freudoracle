```
   ╔═══════════════════════════════════════════════════════════════╗
   ║                                                               ║
   ║    ██████╗ ██████╗  █████╗  ██████╗██╗     ███████╗           ║
   ║   ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║     ██╔════╝           ║
   ║   ██║   ██║██████╔╝███████║██║     ██║     █████╗             ║
   ║   ██║   ██║██╔══██╗██╔══██║██║     ██║     ██╔══╝             ║
   ║   ╚██████╔╝██║  ██║██║  ██║╚██████╗███████╗███████╗           ║
   ║    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝           ║
   ║                                                               ║
   ║        🔮 AI-Powered Telegram Oracle Bot 🔮                   ║
   ║    Объединение древней мудрости и современного AI            ║
   ║                                                               ║
   ╚═══════════════════════════════════════════════════════════════╝
```

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

---

## 🌟 О проекте

**Oracle Bot** - это уникальный Telegram-бот, который объединяет три древние системы гадания с мощью современного искусственного интеллекта:

- 📖 **И-Цзин (Книга Перемен)** - древнекитайская система с 64 гексаграммами
- 🎴 **Таро** - 22 Старших Аркана с глубокими архетипическими значениями
- ⭐ **Хорарная астрология** - астрологический анализ момента вопроса

Бот не просто генерирует случайные ответы - он использует **GPT-4/Claude** для синтеза всех трёх методов в единое мудрое послание, написанное в стиле древнего Оракула.

### ✨ Ключевые особенности

- 🔮 **Тройное гадание**: И-Цзин + Таро + Хорарная астрология
- 🤖 **AI интерпретация**: OpenAI GPT-4 или Anthropic Claude
- 🧘 **Психологические ритуалы**: По методу Бронислава Виногродского
- 💬 **Уточняющие вопросы**: Диалог с Оракулом
- 🎤 **Голосовые сообщения**: Задавай вопросы голосом (в разработке)
- 💰 **Freemium модель**: 3 бесплатных вопроса в день

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11 или выше
- Telegram Bot Token ([получить здесь](https://t.me/botfather))
- OpenAI API Key ([получить здесь](https://platform.openai.com/))

### Установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/oracle-bot.git
cd oracle-bot

# 2. Создайте виртуальное окружение
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Настройте окружение
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Отредактируйте .env и добавьте свои ключи:
# TELEGRAM_BOT_TOKEN=your_bot_token_here
# OPENAI_API_KEY=your_openai_key_here

# 5. Инициализируйте проект
python init_project.py

# 6. Запустите тесты
python test_oracle.py

# 7. Запустите бота
python main.py
```

**Подробная инструкция**: См. [QUICKSTART.md](QUICKSTART.md)

---
