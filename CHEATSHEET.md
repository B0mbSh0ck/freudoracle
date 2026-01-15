# 🚀 Oracle Bot - Шпаргалка

## ⚡ Быстрый старт (5 минут)

```bash
# 1. Клонировать/скачать проект
cd c:\Users\LENOVO\555\orc

# 2. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить .env
copy .env.example .env
# Отредактируйте .env - добавьте токены!

# 5. Инициализация
python init_project.py

# 6. Тест
python test_oracle.py

# 7. Запуск
python main.py
```

---

## 🔑 Получение API ключей

### Telegram Bot Token
1. Открыть [@BotFather](https://t.me/botfather)
2. `/newbot`
3. Скопировать токен → `.env`

### OpenAI API Key
1. [platform.openai.com](https://platform.openai.com)
2. API Keys → Create new
3. Скопировать → `.env`

### Альтернатива: Anthropic Claude
1. [console.anthropic.com](https://console.anthropic.com)
2. API Keys → Create
3. Скопировать → `.env`

---

## 📝 Основные команды

```bash
# Инициализация проекта
python init_project.py

# Тестирование модулей
python test_oracle.py

# Запуск бота
python main.py

# Активация venv (Windows)
venv\Scripts\activate

# Деактивация venv
deactivate

# Обновление зависимостей
pip install --upgrade -r requirements.txt
```

---

## 🤖 Команды бота в Telegram

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу с ботом |
| `/ask` | Задать вопрос Оракулу |
| `/ritual` | Получить психологический ритуал |
| `/stats` | Посмотреть статистику |
| `/help` | Получить помощь |

---

## 📂 Важные файлы

| Файл | Назначение |
|------|------------|
| `main.py` | Запуск Telegram бота |
| `.env` | Секретные ключи (СОЗДАТЬ!) |
| `test_oracle.py` | Тестирование |
| `requirements.txt` | Зависимости |
| `data/iching_hexagrams.json` | База И-Цзин |

---

## 🔧 Конфигурация .env

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# AI (выбрать один)
OPENAI_API_KEY=sk-...
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo-preview

# ИЛИ
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=anthropic
AI_MODEL=claude-3-opus-20240229

# База данных
DATABASE_URL=sqlite:///./oracle.db

# Прочее
DEBUG_MODE=false
LOG_LEVEL=INFO
FREE_QUESTIONS_PER_DAY=3
```

---

## 🐛 Troubleshooting

### Ошибка: "Module not found"
```bash
# Проверьте что вы в правильной директории
pwd  # должно быть .../orc

# Проверьте venv
which python  # должно быть .../venv/...
```

### Ошибка: "Invalid API key"
```bash
# Проверьте .env файл
cat .env  # (Linux/Mac)
type .env  # (Windows)

# Убедитесь что ключ правильный
```

### Ошибка: "pyswisseph not found"
```bash
pip uninstall pyswisseph
pip install pyswisseph==2.10.3.2
```

### Бот не отвечает
```bash
# 1. Проверьте что бот запущен
# 2. Проверьте логи
tail -f logs/bot.log  # (Linux/Mac)
type logs\bot.log  # (Windows)

# 3. Проверьте интернет
# 4. Проверьте токен бота
```

---

## 📊 Тестирование

```bash
# Полный тест всех модулей
python test_oracle.py

# Тест отдельного модуля (в Python REPL)
python
>>> from oracle.iching.iching import iching
>>> primary, secondary = iching.cast_coins()
>>> print(iching.format_hexagram(primary))
```

---

## 🎨 Кастомизация

### Изменить стиль ответов
Файл: `oracle/interpreter.py`
```python
system_prompt = f"""Ты - мудрый Оракул...
СТИЛЬ ОБЩЕНИЯ:
- [ЗДЕСЬ ВАШИ НАСТРОЙКИ]
"""
```

### Добавить карты Таро
Файл: `oracle/tarot/tarot.py`
Метод: `_create_deck()`

### Добавить гексаграммы
Файл: `data/iching_hexagrams.json`

---

## 💰 Монетизация

### Включить премиум
1. Получите токен платежного провайдера (ЮKassa)
2. Добавьте в `.env`:
   ```
   PAYMENT_PROVIDER_TOKEN=your_token
   PREMIUM_PRICE_RUB=499
   ```

### Настроить лимиты
В `.env`:
```
FREE_QUESTIONS_PER_DAY=3
```

---

## 🚀 Развертывание на сервере

### Ubuntu VPS
```bash
# 1. Подклю��итесь к серверу
ssh user@your-server.com

# 2. Установите Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv

# 3. Скопируйте проект
scp -r orc/ user@your-server.com:/home/user/

# 4. На сервере
cd /home/user/orc
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Создайте systemd service
sudo nano /etc/systemd/system/oracle-bot.service

# 6. Запустите
sudo systemctl start oracle-bot
sudo systemctl enable oracle-bot

# 7. Проверьте статус
sudo systemctl status oracle-bot
```

### Docker (опционально)
```bash
# Создайте Dockerfile (см. PROJECT_STRUCTURE.md)
docker build -t oracle-bot .
docker run -d --env-file .env oracle-bot
```

---

## 📈 Мониторинг

```bash
# Логи в реальном времени
tail -f logs/bot.log

# Статус бота (если systemd)
sudo systemctl status oracle-bot

# Рестарт
sudo systemctl restart oracle-bot
```

---

## 📚 Документация

| Файл | Содержание |
|------|------------|
| `README.md` | Общее описание |
| `QUICKSTART.md` | Быстрый старт |
| `ROADMAP.md` | План развития |
| `EXAMPLES.md` | Примеры использования |
| `PROJECT_STRUCTURE.md` | Структура проекта |

---

## 🔗 Полезные ссылки

- Telegram Bot API: https://core.telegram.org/bots/api
- OpenAI API: https://platform.openai.com/docs
- Anthropic Claude: https://docs.anthropic.com
- Swiss Ephemeris: https://www.astro.com/swisseph/
- Python Telegram Bot: https://python-telegram-bot.org/

---

## 💡 Советы

1. **Начните с малого** - протестируйте локально
2. **Соберите фидбек** - первые пользователи очень важны
3. **Оптимизируйте промпты** - ответы должны быть "магическими"
4. **Мониторьте расходы** - OpenAI стоит денег
5. **Backups** - регулярно сохраняйте БД

---

## ⚠️ Важно помнить

- ✅ НЕ коммитьте `.env` в git
- ✅ Используйте strong API keys
- ✅ Регулярно обновляйте зависимости
- ✅ Мониторьте логи на ошибки
- ✅ Тестируйте перед деплоем

---

## 📞 Помощь

1. Проверьте `logs/bot.log`
2. Запустите `python test_oracle.py`
3. Проверьте GitHub Issues (если есть)
4. Создайте Issue с описанием проблемы

---

**Последнее обновление:** 2026-01-15  
**Версия:** 1.0.0-MVP

🔮 Удачи с вашим Оракулом! 🔮
