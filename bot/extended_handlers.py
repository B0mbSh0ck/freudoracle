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
        
    # Обработка снов
    if context.user_data.get('awaiting_dream'):
        await process_dream_interpretation(update, context, text)
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
        
        # Парсим дату и время (более гибко через регулярки)
        import re
        date_match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', date_str)
        time_match = re.search(r'(\d{1,2}):(\d{1,2})', time_str)
        
        if not date_match:
            raise ValueError("Неверный формат даты. Используйте дд.мм.гггг")
            
        day, month, year = map(int, date_match.groups())
        if year < 100: year += 2000 # Для двузначных годов
        
        hour, minute = 12, 0
        if time_match:
            hour, minute = map(int, time_match.groups())
        
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
        # Парсим дату более гибко через регулярные выражения
        date_str = text.strip()
        match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', date_str)
        if not match:
            raise ValueError("Неверный формат даты. Используйте дд.мм.гггг")
            
        day, month, year = map(int, match.groups())
        if year < 100: year += 2000
        
        try:
            birth_date = datetime(year, month, day)
        except ValueError:
            await message.reply_text(
                "❌ Такой даты не существует в календаре.\n\n"
                "Проверьте правильность даты и попробуйте снова.\n"
                "Формат: дд.мм.гггг"
            )
            return
        
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
        # Парсим дату более гибко
        date_str = text.strip()
        import re
        match = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', date_str)
        if not match:
            raise ValueError("Неверный формат даты. Используйте дд.мм.гггг")
            
        day, month, year = map(int, match.groups())
        if year < 100: year += 2000
        
        try:
            birth_date = datetime(year, month, day)
        except ValueError:
            await message.reply_text(
                "❌ Такой даты не существует в календаре.\\n\\n"
                "Проверьте правильность даты и попробуйте снова.\\n"
                "Формат: дд.мм.гггг"
            )
            return
        
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
        dates = re.findall(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', text)
        
        if len(dates) != 2:
            await message.reply_text(
                "❌ Мне нужны ровно две даты для анализа.\n"
                "Пример: `15.03.1990 20.01.1995`",
                parse_mode='Markdown'
            )
            return
            
        # Формируем объекты datetime
        parsed_dates = []
        for idx, d_parts in enumerate(dates, 1):
            day, month, year = map(int, d_parts)
            if year < 100: year += 2000
            try:
                parsed_dates.append(datetime(year, month, day))
            except ValueError:
                await message.reply_text(
                    f"❌ Дата #{idx} невозможна ({day}.{month}.{year}).\\n\\n"
                    "Проверьте правильность дат и попробуйте снова.\\n"
                    "Пример: `15.03.1990 20.01.1995`",
                    parse_mode='Markdown'
                )
                return
            
        dt1, dt2 = parsed_dates
        d1_str = dt1.strftime('%d.%m.%Y')
        d2_str = dt2.strftime('%d.%m.%Y')
        
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


async def show_tarot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню выбора сферы для расклада Таро"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("🔮 Свой вопрос", callback_data="ask")],
        [InlineKeyboardButton("🏥 Здоровье", callback_data="tarot_sphere_health"), InlineKeyboardButton("💼 Карьера", callback_data="tarot_sphere_career")],
        [InlineKeyboardButton("💞 Любовь", callback_data="tarot_sphere_love"), InlineKeyboardButton("💰 Деньги", callback_data="tarot_sphere_money")],
        [InlineKeyboardButton("🎯 Предназначение", callback_data="tarot_sphere_purpose")],
        [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
    ]
    
    text = "🃏 *РАСКЛАД ТАРО «ТРИ КАРТЫ»*\n\nВыбери сферу жизни, которую хочешь осветить сегодня. Оракул вытянет три аркана и прочтет их тайный смысл для тебя."
    
    if query:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def process_tarot_spread(update: Update, context: ContextTypes.DEFAULT_TYPE, sphere: str):
    """Выполнить расклад Таро (3 карты)"""
    from oracle.tarot.tarot import tarot
    from oracle.interpreter import oracle_interpreter
    import random
    import copy
    
    query = update.callback_query
    user = update.effective_user
    db_user = user_manager.get_or_create_user(user)
    
    # 1. Проверка лимитов
    allowed, result = user_manager.check_tarot_limit(user.id)
    if not allowed:
        keyboard = [[InlineKeyboardButton("💎 Купить Премиум", callback_data="premium")]]
        await query.message.reply_text(
            f"🪫 *Энергия Таро исчерпана*\n\n{result}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return

    await query.message.reply_text(f"🃏 Перетасовываю колоду... Обращаюсь к Арканам ({sphere.upper()}).")
    
    # 2. Тянем 3 карты (делаем копии чтобы не менять оригиналы в синглтоне)
    all_cards = list(tarot.deck.cards)
    selected_cards = random.sample(all_cards, 3)
    
    cards = []
    for c in selected_cards:
        card_copy = copy.copy(c)
        card_copy.is_reversed = random.choice([True, False])
        cards.append(card_copy)

    # 3. Формируем текст расклада
    cards_display = []
    for i, c in enumerate(cards):
        pos = ["Первая карта (Основа)", "Вторая карта (Путь)", "Третья карта (Итог)"][i]
        cards_display.append(f"📍 *{pos}:*\n{tarot.deck.format_card(c)}")
    
    await query.message.reply_text(f"✨ *Твой расклад:*\n\n" + "\n\n".join(cards_display), parse_mode='Markdown')
    
    # 4. Интерпретация AI
    await query.message.reply_text("⏳ Оракул всматривается в образы...")
    
    # Подготавливаем данные для AI
    interpretation = await oracle_interpreter.get_tarot_spread_interpretation(
        sphere, cards, user.first_name, db_user.is_premium
    )
    
    # 5. Кнопки
    keyboard = [
        [InlineKeyboardButton("👍 Полезно", callback_data="rate_good"), InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")]
    ]
    
    # Кнопка "Подробнее" только для премиума
    if db_user.is_premium:
        keyboard.append([InlineKeyboardButton("📜 Узнать подробнее", callback_data="deepen")])
        # Сохраняем в контекст для "deepen"
        context.user_data['last_question'] = f"Расклад Таро на сферу: {sphere}"
        context.user_data['last_oracle_response'] = {
            'interpretation': interpretation,
            'tarot_cards': cards
        }
    
    keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu")])
    
    await query.message.reply_text(
        f"📜 *ТВОЙ ПРОГНОЗ:*\n\n{fix_markdown(interpretation)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def process_dream_interpretation(update: Update, context: ContextTypes.DEFAULT_TYPE, dream_text: str):
    """Начальная трактовка сна"""
    context.user_data['awaiting_dream'] = False
    message = update.message if update.message else update.callback_query.message
    user = update.effective_user
    
    await message.reply_text("😴 Оракул погружается в твой сон... Обращаюсь к тайным сонникам.")
    
    from oracle.interpreter import oracle_interpreter
    interpretation = await oracle_interpreter.interpret_dream(dream_text, user.first_name)
    
    # Сохраняем сон для "подробно"
    context.user_data['last_dream'] = dream_text
    
    keyboard = [
        [InlineKeyboardButton("📜 Подробно (AI + Личные данные)", callback_data="dream_detailed")],
        [InlineKeyboardButton("👍 Полезно", callback_data="rate_good"), InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")],
        [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
    ]
    
    await message.reply_text(
        f"🌙 *ТРАКТОВКА ТВОЕГО СНА:*\n\n{fix_markdown(interpretation)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def process_dream_detailed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подробная трактовка сна с учетом личных данных"""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    db_user = user_manager.get_or_create_user(user)
    
    try:
        # 1. Проверка лимита
        allowed, message = user_manager.check_dream_detailed_limit(user.id)
        if not allowed:
            await query.answer(message, show_alert=True)
            return

        dream_text = context.user_data.get('last_dream')
        if not dream_text:
            await query.message.reply_text("⚠️ Сон утерян. Напиши его еще раз.")
            return

        processing_msg = await query.message.reply_text("🔮 Глубокое погружение... Совмещаю образы сна с твоей судьбой.")
        
        # 2. Собираем личные данные
        from oracle.horoscope.moon_parser import moon_parser
        moon_info = await moon_parser.get_moon_info()
        
        user_data = user_manager.get_user_data(user.id)
        sucai_info = ""
        if user_data and user_data.birth_date:
            from oracle.numerology.sucai import chinese_numerology
            sucai = chinese_numerology.calculate_sucai(user_data.birth_date)
            # В Сюцай soul - это число сознания, life_path - это миссия
            sucai_info = f"Число Сознания {sucai.soul}, Миссия {sucai.life_path}"

        personal_data = {
            'birth_date': user_data.birth_date.strftime('%d.%m.%Y') if user_data and user_data.birth_date else "Не указана",
            'zodiac_sign': user_data.zodiac_sign if user_data else "Не указан",
            'sucai': sucai_info,
            'lunar_day': moon_info.lunar_day if moon_info else "Неизвестно"
        }

        # 3. AI интерпретация
        from oracle.interpreter import oracle_interpreter
        detailed_interpretation = await oracle_interpreter.interpret_dream(dream_text, user.first_name, is_premium=db_user.is_premium, personal_data=personal_data)
        
        # 4. Кнопки (с возможностью уточнений)
        keyboard = [
            [InlineKeyboardButton("🔍 Уточнить детали", callback_data="ask_details_dream")],
            [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
        ]
        
        # Сохраняем для уточнений
        context.user_data['last_question'] = f"Трактовка сна: {dream_text}"
        context.user_data['last_oracle_response'] = {'interpretation': detailed_interpretation}
        context.user_data['followup_count'] = 0

        await processing_msg.delete()
        await query.message.reply_text(
            f"🌌 *ГЛУБОКИЙ АНАЛИЗ СНА:*\n\n{fix_markdown(detailed_interpretation)}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in process_dream_detailed: {e}")
        await query.message.reply_text(f"❌ Туман сгустился... Ошибка глубинного анализа: {str(e)}")
