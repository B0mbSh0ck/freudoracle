"""
Расширенные обработчики для новых модулей Oracle Bot
"""
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import re

from oracle.natal.natal_chart import natal_astrology
from oracle.numerology.sucai import chinese_numerology
from oracle.matrix.destiny_matrix import matrix_of_destiny
from oracle.horoscope.horoscope_parser import horoscope_parser


async def handle_awaiting_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Обработка ожидаемых данных от пользователя
    Returns True если сообщение было обработано как ожидаемые данные
    """
    
    text = update.message.text
    
    # Обработка натальной карты
    if context.user_data.get('awaiting_natal_data'):
        await process_natal_data(update, context, text)
        return True
    
    # Обработка нумерологии
    if context.user_data.get('awaiting_numerology_date'):
        await process_numerology_date(update, context, text)
        return True
    
    # Обработка матрицы судьбы
    if context.user_data.get('awaiting_matrix_date'):
        await process_matrix_date(update, context, text)
        return True
    
    return False


async def process_natal_data(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка данных для натальной карты"""
    context.user_data['awaiting_natal_data'] = False
    
    try:
        # Парсим входные данные
        # Формат: 15.03.1990 14:30 Москва
        parts = text.strip().split()
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Неверный формат. Используйте: `дд.мм.гггг чч:мм город`\n"
                "Пример: `15.03.1990 14:30 Москва`",
                parse_mode='Markdown'
            )
            return
        
        # Парсим дату
        date_str = parts[0]
        time_str = parts[1] if len(parts) > 1 else "12:00"
        location = parts[2] if len(parts) > 2 else "Москва"
        
        # Координаты по умолчанию (Москва)
        latitude = 55.75
        longitude = 37.62
        
        # Если указан не Москва, все равно используем Москву (можно расширить)
        # TODO: Добавить геокодинг городов
        
        # Парсим дату и время
        day, month, year = map(int, date_str.split('.'))
        hour, minute = map(int, time_str.split(':'))
        
        birth_date = datetime(year, month, day, hour, minute)
        
        # Рассчитываем натальную карту
        await update.message.reply_text("🌟 Рассчитываю вашу натальную карту...")
        
        natal_chart = natal_astrology.calculate_natal_chart(
            birth_date=birth_date,
            latitude=latitude,
            longitude=longitude,
            location=location
        )
        
        # Форматируем и отправляем
        formatted = natal_astrology.format_natal_chart(natal_chart)
        await update.message.reply_text(formatted, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при расчете натальной карты: {str(e)}\n\n"
            "Проверьте формат данных и попробуйте снова.\n"
            "Используйте /natal чтобы начать заново."
        )


async def process_numerology_date(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка даты для нумерологии"""
    context.user_data['awaiting_numerology_date'] = False
    
    try:
        # Парсим дату
        date_str = text.strip()
        day, month, year = map(int, date_str.split('.'))
        
        birth_date = datetime(year, month, day)
        
        # Рассчитываем числа Сюцай
        await update.message.reply_text("🔢 Рассчитываю ваши числа судьбы...")
        
        sucai = chinese_numerology.calculate_sucai(birth_date)
        
        # Форматируем и отправляем
        formatted = chinese_numerology.format_sucai(sucai)
        await update.message.reply_text(formatted, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при расчете нумерологии: {str(e)}\n\n"
            "Проверьте формат даты (дд.мм.гггг) и попробуйте снова.\n"
            "Используйте /numerology чтобы начать заново."
        )


async def process_matrix_date(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка даты для матрицы судьбы"""
    context.user_data['awaiting_matrix_date'] = False
    
    try:
        # Парсим дату
        date_str = text.strip()
        day, month, year = map(int, date_str.split('.'))
        
        birth_date = datetime(year, month, day)
        
        # Рассчитываем матрицу
        await update.message.reply_text("🔮 Рассчитываю вашу матрицу судьбы...")
        
        matrix = matrix_of_destiny.calculate_matrix(birth_date)
        
        # Форматируем и отправляем
        formatted = matrix_of_destiny.format_matrix(matrix)
        
        # Так как матрица может быть длинной, отправляем частями если нужно
        if len(formatted) > 4000:
            # Разбиваем на части
            parts = [formatted[i:i+4000] for i in range(0, len(formatted), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(formatted, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при расчете матрицы: {str(e)}\n\n"
            "Проверьте формат даты (дд.мм.гггг) и попробуйте снова.\n"
            "Используйте /matrix чтобы начать заново."
        )


async def handle_horoscope_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, sign: str):
    """Обработка выбора знака зодиака для гороскопа"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Получаем гороскоп
        await query.message.reply_text(f"⭐ Получаю гороскоп для знака {sign.capitalize()}...")
        
        horoscope = await horoscope_parser.get_horoscope(
            sign=sign,
            period='today',
            use_fallback=True  # Пока используем fallback, пока парсинг не настроен
        )
        
        # Форматируем и отправляем
        formatted = horoscope_parser.format_horoscope(horoscope)
        await query.message.reply_text(formatted, parse_mode='Markdown')
        
    except Exception as e:
        await query.message.reply_text(
            f"❌ Ошибка при получении гороскопа: {str(e)}\n\n"
            "Попробуйте позже."
        )
