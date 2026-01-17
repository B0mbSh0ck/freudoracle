"""
Расширенные обработчики для новых модулей Oracle Bot
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import re

from oracle.natal.natal_chart import natal_astrology
from oracle.numerology.sucai import chinese_numerology
from oracle.matrix.destiny_matrix import matrix_of_destiny
from oracle.horoscope.horoscope_parser import horoscope_parser
from oracle.compatibility.compatibility import compatibility
from database.user_manager import user_manager
from utils import fix_markdown


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
    
    # Обработка совместимости
    if context.user_data.get('awaiting_compatibility_dates'):
        await process_compatibility_dates(update, context, text)
        return True
    
    return False


async def process_natal_data(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка данных для натальной карты"""
    context.user_data['awaiting_natal_data'] = False
    message = update.message if update.message else update.callback_query.message
    
    try:
        # Парсим входные данные
        # Формат: 15.03.1990 14:30 Москва
        parts = text.strip().split()
        
        if len(parts) < 2:
            await message.reply_text(
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
        await message.reply_text("🌟 Рассчитываю вашу натальную карту...")
        
        natal_chart = natal_astrology.calculate_natal_chart(
            birth_date=birth_date,
            latitude=latitude,
            longitude=longitude,
            location=location
        )
        
        # Сохраняем данные пользователя в БД
        user_sign_en = horoscope_parser.get_sign_from_date(birth_date.day, birth_date.month)
        user_sign_ru = horoscope_parser.SIGN_NAMES_RU.get(user_sign_en)
        
        user_manager.save_user_data(
            telegram_id=update.effective_user.id,
            birth_date=birth_date,
            birth_time=time_str,
            birth_location=location,
            zodiac_sign=user_sign_ru
        )
        
        # Также обновляем в контексте для текущей сессии
        context.user_data['user_info'] = {
            'birth_date': birth_date,
            'date_str': date_str,
            'time_str': time_str,
            'location': location
        }
        
        # Кнопки для результатов
        keyboard = [
            [
                InlineKeyboardButton("🏥 Здоровье (Free)", callback_data="sphere_health"),
                InlineKeyboardButton("💼 Карьера (Free)", callback_data="sphere_career")
            ],
            [
                InlineKeyboardButton("💞 Любовь (Premium)", callback_data="sphere_love"),
                InlineKeyboardButton("💰 Деньги (Premium)", callback_data="sphere_money")
            ],
            [
                InlineKeyboardButton("🎯 Предназначение (Premium)", callback_data="sphere_purpose")
            ],
            [InlineKeyboardButton("👍 Полезно", callback_data="rate_good"), InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")],
            [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
        ]
        
        # Сохраняем тип и данные для интерпретации сфер
        context.user_data['last_calc_type'] = 'natal'
        context.user_data['last_calc_data'] = {
            'date': date_str,
            'time': time_str,
            'location': location
        }
        
        # Форматируем и отправляем
        formatted = natal_astrology.format_natal_chart(natal_chart)
        await message.reply_text(
            fix_markdown(formatted), 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Добавляем подсказку
        await message.reply_text("💡 Данные сохранены. Теперь можно использовать их для других расчетов.")        
    except Exception as e:
        import logging
        logging.error(f"Error in process_natal_data: {e}")
        await message.reply_text(
            f"❌ Ошибка при расчете натальной карты: {str(e)}\n\n"
            "Проверьте формат данных и попробуйте снова.\n"
            "Используйте /natal чтобы начать заново."
        )


async def process_numerology_date(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка даты для нумерологии"""
    context.user_data['awaiting_numerology_date'] = False
    message = update.message if update.message else update.callback_query.message
    
    try:
        # Парсим дату
        date_str = text.strip()
        day, month, year = map(int, date_str.split('.'))
        
        birth_date = datetime(year, month, day)
        
        # Рассчитываем числа Сюцай
        await message.reply_text("🔢 Рассчитываю ваши числа судьбы...")
        
        sucai = chinese_numerology.calculate_sucai(birth_date)
        
        # Сохраняем дату рождения в БД
        user_manager.save_user_data(
            telegram_id=update.effective_user.id,
            birth_date=birth_date
        )
        
        # Обновляем в контексте
        if 'user_info' not in context.user_data:
            context.user_data['user_info'] = {}
        context.user_data['user_info']['birth_date'] = birth_date
        context.user_data['user_info']['date_str'] = date_str
        
        # Кнопки для результатов
        keyboard = [
            [
                InlineKeyboardButton("🏥 Здоровье (Free)", callback_data="sphere_health"),
                InlineKeyboardButton("💼 Карьера (Free)", callback_data="sphere_career")
            ],
            [
                InlineKeyboardButton("💞 Любовь (Premium)", callback_data="sphere_love"),
                InlineKeyboardButton("💰 Деньги (Premium)", callback_data="sphere_money")
            ],
            [
                InlineKeyboardButton("🎯 Предназначение (Premium)", callback_data="sphere_purpose")
            ],
            [InlineKeyboardButton("👍 Полезно", callback_data="rate_good"), InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")],
            [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
        ]
        
        # Сохраняем тип и данные для интерпретации сфер
        context.user_data['last_calc_type'] = 'numerology'
        context.user_data['last_calc_data'] = {'date': date_str}
        
        # Форматируем и отправляем
        formatted = chinese_numerology.format_sucai(sucai)
        await message.reply_text(
            fix_markdown(formatted), 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        import logging
        logging.error(f"Error in process_numerology_date: {e}")
        await message.reply_text(
            f"❌ Ошибка при расчете нумерологии: {str(e)}\n\n"
            "Проверьте формат даты (дд.мм.гггг) и попробуйте снова.\n"
            "Используйте /numerology чтобы начать заново."
        )


async def process_matrix_date(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка даты для матрицы судьбы"""
    context.user_data['awaiting_matrix_date'] = False
    message = update.message if update.message else update.callback_query.message
    
    try:
        # Парсим дату
        date_str = text.strip()
        day, month, year = map(int, date_str.split('.'))
        
        birth_date = datetime(year, month, day)
        
        # Рассчитываем матрицу
        await message.reply_text("🔮 Рассчитываю вашу матрицу судьбы...")
        
        matrix = matrix_of_destiny.calculate_matrix(birth_date)
        
        # Сохраняем дату в БД
        user_manager.save_user_data(
            telegram_id=update.effective_user.id,
            birth_date=birth_date
        )
        
        # Сохраняем дату в контексте
        if 'user_info' not in context.user_data:
            context.user_data['user_info'] = {}
        context.user_data['user_info']['birth_date'] = birth_date
        context.user_data['user_info']['date_str'] = date_str

        # Форматируем и отправляем
        formatted = matrix_of_destiny.format_matrix(matrix)
        
        # Кнопки для результатов
        keyboard = [
            [
                InlineKeyboardButton("🏥 Здоровье (Free)", callback_data="sphere_health"),
                InlineKeyboardButton("💼 Карьера (Free)", callback_data="sphere_career")
            ],
            [
                InlineKeyboardButton("💞 Любовь (Premium)", callback_data="sphere_love"),
                InlineKeyboardButton("💰 Деньги (Premium)", callback_data="sphere_money")
            ],
            [
                InlineKeyboardButton("🎯 Предназначение (Premium)", callback_data="sphere_purpose")
            ],
            [InlineKeyboardButton("👍 Полезно", callback_data="rate_good"), InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")],
            [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
        ]
        
        # Сохраняем тип и данные для интерпретации сфер
        context.user_data['last_calc_type'] = 'matrix'
        context.user_data['last_calc_data'] = {'date': date_str}

        # Так как матрица может быть длинной, отправляем частями если нужно
        if len(formatted) > 4000:
            parts = [formatted[i:i+4000] for i in range(0, len(formatted), 4000)]
            for i, part in enumerate(parts):
                # Клавиатура только к последнему сообщению
                markup = InlineKeyboardMarkup(keyboard) if i == len(parts)-1 else None
                await message.reply_text(part, parse_mode='Markdown', reply_markup=markup)
        else:
            await message.reply_text(formatted, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        
    except Exception as e:
        import logging
        logging.error(f"Error in process_matrix_date: {e}")
        await message.reply_text(
            f"❌ Ошибка при расчете матрицы: {str(e)}\n\n"
            "Проверьте формат даты (дд.мм.гггг) и попробуйте снова.\n"
            "Используйте /matrix чтобы начать заново."
        )


async def handle_horoscope_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, sign: str):
    """Обработка выбора знака зодиака для гороскопа"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Получаем период из контекста (по умолчанию сегодня)
        period = context.user_data.get('temp_horo_period', 'today')
        
        horoscope = await horoscope_parser.get_horoscope(
            sign=sign,
            period=period
        )
        
        # Форматируем и отправляем
        formatted = horoscope_parser.format_horoscope(horoscope)
        
        keyboard = [
            [InlineKeyboardButton("👍 Полезно", callback_data="rate_good"), InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")],
            [InlineKeyboardButton("⏳ Другой период", callback_data="horo_menu")],
            [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
        ]
        
        await query.message.reply_text(
            fix_markdown(formatted), 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await query.message.reply_text(
            f"❌ Ошибка при получении гороскопа: {str(e)}\n\n"
            "Попробуйте позже."
        )


async def process_compatibility_dates(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обработка дат для совместимости"""
    context.user_data['awaiting_compatibility_dates'] = False
    message = update.message if update.message else update.callback_query.message
    
    try:
        # Парсим 2 даты
        # Формат: 15.03.1990 20.01.1995
        import re
        dates = re.findall(r'\d{2}\.\d{2}\.\d{4}', text)
        
        if len(dates) != 2:
            await message.reply_text(
                "❌ Мне нужны ровно две даты для анализа.\n"
                "Пример: `15.03.1990 20.01.1995`",
                parse_mode='Markdown'
            )
            return
            
        d1_str, d2_str = dates
        day1, month1, year1 = map(int, d1_str.split('.'))
        day2, month2, year2 = map(int, d2_str.split('.'))
        
        dt1 = datetime(year1, month1, day1)
        dt2 = datetime(year2, month2, day2)
        
        await message.reply_text("💞 Рассчитываю энергии совместимости...")
        
        # Считаем
        result = compatibility.calculate(dt1, dt2)
        
        # Формируем отчет
        speedometer = compatibility.render_speedometer(result['total_score'])
        
        report = f"""
💞 *Совместимость пары:*

{d1_str} + {d2_str}

*Общий уровень:* {speedometer}

*Детали:*
• По числу сознания: {result['details']['sucai']}%
• По матрице судьбы: {result['details']['matrix']}%
• Биоритмика: {result['details']['biorhythm']}%

{result['text_report']}
"""
        # Кнопки
        keyboard = [
            [InlineKeyboardButton("👍 Полезно", callback_data="rate_good"), InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")],
            [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
        ]
        
        await message.reply_text(
            fix_markdown(report), 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        import logging
        logging.error(f"Error in process_compatibility_dates: {e}")
        await message.reply_text(
            f"❌ Ошибка в данных: {e}\n"
            "Попробуй снова: `дд.мм.гггг дд.мм.гггг`"
        )
