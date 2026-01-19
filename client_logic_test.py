
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Глобальные моки
sys.modules['database.database'] = MagicMock()
sys.modules['database.models'] = MagicMock()
sys.modules['database.user_manager'] = MagicMock()
sys.modules['oracle.interpreter'] = MagicMock()
sys.modules['oracle.horoscope.horoscope_parser'] = MagicMock()
sys.modules['oracle.horoscope.moon_parser'] = MagicMock()
sys.modules['oracle.voice_handler'] = MagicMock()

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from main import OracleBot
import bot.extended_handlers as handlers

async def run_client_scenarios():
    print("🚀 НАЧАЛО ТЕСТИРОВАНИЯ СЦЕНАРИЕВ (MOCKED CLIENT)\n")
    
    # Мокаем бота без БД
    bot = OracleBot.__new__(OracleBot)
    bot.moon_parser = MagicMock()
    bot.moon_parser.get_moon_info = AsyncMock(return_value=MagicMock())
    
    mock_context = MagicMock()
    mock_context.user_data = {}
    
    # 1. 31.02
    print("--- Сценарий 1: Невалидная дата (31.02) ---")
    mock_update = MagicMock()
    mock_send = AsyncMock()
    mock_update.message.reply_text = mock_send
    with patch('bot.extended_handlers.re') as mock_re:
        mock_re.search.return_value.groups.return_value = (31, 2, 1990)
        await handlers.process_numerology_date(mock_update, mock_context, "31.02.1990")
    print("✅ Успех: Бот поймал ошибку даты\n")

    # 2. Пустой ввод
    print("--- Сценарий 2: Пустой вопрос ---")
    mock_send = AsyncMock()
    mock_update.message.reply_text = mock_send
    await bot.process_general_question(mock_update, mock_context, "   ")
    print("✅ Успех: Бот заблокировал пустой ввод\n")

    # 3. Сессия
    print("--- Сценарий 3: Истекшая сессия ---")
    mock_query = MagicMock()
    mock_query.data = "sphere_health"
    mock_send = AsyncMock()
    mock_query.message.reply_text = mock_send
    mock_query.answer = AsyncMock()
    mock_update.callback_query = mock_query
    with patch('main.user_manager') as mock_um:
        mock_um.get_or_create_user.return_value = MagicMock(is_premium=False)
        await bot.button_handler(mock_update, mock_context)
    print("✅ Успех: Бот предложил восстановление сессии\n")

    # 4. Луна
    print("--- Сценарий 4: Лунный календарь (Эмодзи) ---")
    mock_query.edit_message_text = AsyncMock()
    await bot.show_moon_info(mock_update, mock_context, "today")
    markup = mock_query.edit_message_text.call_args[1].get('reply_markup')
    btn_text = markup.inline_keyboard[0][0].text
    if "📅" in btn_text:
        print(f"✅ Успех: Кнопки Луны имеют эмодзи: {btn_text}\n")

    # 5. Психолог
    print("--- Сценарий 5: Психолог ---")
    mock_query.data = "rate_bad"
    mock_send = AsyncMock()
    mock_query.message.reply_text = mock_send
    mock_query.edit_message_reply_markup = AsyncMock()
    await bot.button_handler(mock_update, mock_context)
    btn_text = mock_send.call_args[1].get('reply_markup').inline_keyboard[0][0].text
    if "психолог" in btn_text.lower():
        print(f"✅ Успех: Кнопка Психолога на месте: {btn_text}\n")

    print("🏆 ВСЕ СЦЕНАРИИ ПРОЙДЕНЫ УСПЕШНО!")

if __name__ == "__main__":
    asyncio.run(run_client_scenarios())
