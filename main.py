"""
Главный файл Telegram бота Оракула
"""
import asyncio
from datetime import datetime, time as dt_time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
    filters
)
from loguru import logger
import sys
import os
import tempfile

from config.settings import settings
from oracle.interpreter import oracle_interpreter
from database.models import User, QuestionSession
from database.database import SessionLocal, init_db
from database.user_manager import user_manager
from utils import fix_markdown
from oracle.horoscope.horoscope_parser import horoscope_parser
from oracle.horoscope.moon_parser import moon_parser

# Импорт новых модулей
from bot.extended_handlers import (
    handle_awaiting_data,
    handle_horoscope_callback,
    process_natal_data,
    process_numerology_date,
    process_matrix_date,
    show_tarot_menu,
    process_tarot_spread,
    process_dream_interpretation,
    process_dream_detailed
)
from oracle.voice_handler import voice_handler
from oracle.compatibility.compatibility import compatibility

# Настройка логгирования
logger.remove()
logger.add(sys.stderr, level=settings.log_level)
logger.add("logs/bot.log", rotation="1 day", retention="7 days", level="INFO")


class OracleBot:
    """Telegram бот Оракула"""
    
    def __init__(self):
        self.app = Application.builder().token(settings.telegram_bot_token).build()
        self._setup_handlers()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Настройка периодических задач"""
        if self.app.job_queue:
            # Каждый день в 6:00 утра (UTC)
            self.app.job_queue.run_daily(self.daily_mailing_job, time=dt_time(hour=6, minute=0))
            logger.info("Daily mailing job scheduled at 06:00 UTC")

    async def daily_mailing_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Задача ежедневной рассылки прогнозов"""
        logger.info("Starting daily mailing job...")
        session = SessionLocal()
        try:
            # Находим всех активных пользователей с включенной рассылкой
            users = session.query(User).filter(User.daily_prediction_enabled == True).all()
            
            # Генерируем общее послание дня (чтобы не дергать AI для каждого)
            guidance = await oracle_interpreter.get_daily_guidance()
            formatted_guidance = fix_markdown(guidance)
            
            # Кнопки для рассылки
            keyboard = [
                [InlineKeyboardButton("🔮 Задать вопрос", callback_data="ask")],
                [InlineKeyboardButton("✨ Другие возможности", callback_data="menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            count = 0
            for db_user in users:
                try:
                    text = f"📜 *Свиток Дня от Источника*\n\n{formatted_guidance}\n\n✨ Слушай шепот судьбы и делай свой выбор.\n\n🔮 *Если туман сгустился, задай свой вопрос...*"
                    await context.bot.send_message(
                        chat_id=db_user.telegram_id,
                        text=text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    count += 1
                    # Небольшая задержка чтобы не спамить API Telegram
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.warning(f"Could not send daily message to {db_user.telegram_id}: {e}")
            
            logger.info(f"Daily mailing completed. Sent to {count} users.")
        finally:
            session.close()

    def _setup_handlers(self):
        """Настроить обработчики команд и сообщений"""
        # Команды
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("ask", self.ask_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("debug_info", self.debug_info_command))
        self.app.add_handler(CommandHandler("test_ai", self.test_ai_command))
        self.app.add_handler(CommandHandler("force_question", self.force_question_command))
        
        # Новые команды
        self.app.add_handler(CommandHandler("natal", self.natal_command))
        self.app.add_handler(CommandHandler("numerology", self.numerology_command))
        self.app.add_handler(CommandHandler("matrix", self.matrix_command))
        self.app.add_handler(CommandHandler("horoscope", self.horoscope_command))
        self.app.add_handler(CommandHandler("tarot", self.tarot_command))
        self.app.add_handler(CommandHandler("compatibility", self.compatibility_command))
        self.app.add_handler(CommandHandler("dream", self.dream_command))
        
        # Callback кнопки
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Текстовые сообщения
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Платежи и премиум
        self.app.add_handler(CommandHandler("premium", self.premium_command))
        self.app.add_handler(CommandHandler("referral", self.referral_command))
        self.app.add_handler(CommandHandler("setpremium", self.set_premium_command)) # Для тестов
        self.app.add_handler(PreCheckoutQueryHandler(self.precheckout_callback))
        self.app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment_callback))
        
        # Голосовые сообщения
        self.app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
    
    async def debug_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """DEBUG: Show internal configuration"""
        try:
            interp = oracle_interpreter
            
            groq_key = settings.groq_api_key
            openai_key = settings.openai_api_key
            
            censored_groq = f"{groq_key[:4]}...{groq_key[-4:]}" if groq_key else "None"
            censored_openai = f"{openai_key[:4]}...{openai_key[-4:]}" if openai_key else "None"
            
            is_groq = getattr(interp, 'is_groq', False)
            
            msg = (
                f"🐞 *DEBUG INFO*\n"
                f"Config Provider: `{settings.ai_provider}`\n"
                f"Active Provider: `{interp.ai_provider}`\n"
                f"Is Groq Mode: `{is_groq}`\n"
                f"Model: `{interp.model}`\n"
                f"Groq Key: `{censored_groq}`\n"
                f"OpenAI Key: `{censored_openai}`\n"
                f"Base URL: `{interp.client.base_url}`"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"Debug Error: {e}")

    async def test_ai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """DEBUG: Test AI generation directly"""
        try:
            interp = oracle_interpreter
            await update.message.reply_text(f"🧪 Testing AI...\nProvider: {interp.ai_provider}\nModel: {interp.model}")
            
            if interp.ai_provider == "openai":
                response = interp.client.chat.completions.create(
                    model=interp.model,
                    messages=[{"role": "user", "content": "Just say 'Works!'"}],
                    max_tokens=10
                )
                result = response.choices[0].message.content
            elif interp.ai_provider == "anthropic":
                response = interp.client.messages.create(
                    model=interp.model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Just say 'Works!'"}]
                )
                result = response.content[0].text
            else:
                 result = "Unknown provider"
                 
            await update.message.reply_text(f"✅ SUCCESS: {result}")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            # Send error in chunks if too long
            await update.message.reply_text(f"❌ ERROR:\n{e}")
            if len(tb) < 3000:
                await update.message.reply_text(f"Traceback:\n`{tb}`", parse_mode='Markdown')

    async def force_question_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """DEBUG: Force oracle question with full error exposure"""
        try:
            await update.message.reply_text("🧪 Testing FULL Oracle Flow (Iching+Tarot+Horary+AI)...")
            
            interp = oracle_interpreter
            user = update.effective_user
            
            # Force a test question through the FULL oracle stack
            result = await interp.process_question(
                question="Test question", 
                user_name=user.first_name,
                is_premium=False
            )
            
            await update.message.reply_text(f"✅ SUCCESS! Oracle responded.")
            await update.message.reply_text(f"Response preview:\n{result['interpretation'][:500]}...")
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            await update.message.reply_text(f"❌ ORACLE ERROR:\n{e}")
            # Split into chunks if needed
            if len(tb) < 3000:
                await update.message.reply_text(f"```\n{tb}\n```", parse_mode='Markdown')
            else:
                # Send first 3000 chars
                await update.message.reply_text(f"```\n{tb[:3000]}\n```", parse_mode='Markdown')
            
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        self._reset_state(context)
        user = update.effective_user
        query = update.callback_query
        
        welcome_message = f"""
🌀 *ПРИВЕТСТВУЮ В ОБИТЕЛИ ФРЕЙДОРАКУЛА!* 🌀

Здравствуй, {user.first_name}. Ты здесь не случайно — Источник уже начал резонировать с твоим запросом. 🕯

🔮 *ГЛАВНАЯ ТАЙНА: ЗАДАТЬ ВОПРОС*
Это моё основное искусство. Специальный алгоритм объединяет мудрость **И Цзин**, архетипы **Таро** и **Хорарную астрологию**. Ответ будет создан **индивидуально под тебя**, учитывая текущие вибрации Вселенной.

📜 *ПУТИ ПОЗНАНИЯ:*
📡 *Звезды и Числа:* Твой код судьбы (Натальная карта, Сюцай, Матрица).
😴 *Трактовка Снов:* Загляни в глубины своего подсознания.
🃏 *Таро:* Тематический анализ 5 ключевых сфер жизни.
💞 *Энергия связи:* Точный расчет совместимости душ.

⚠️ *Помни:* Оракул дает ключи, но дверь открываешь ты сам. ⚖️

Задай вопрос текстом ⌨️ или голосом 🎙. Я внимаю... 🤫
"""
        
        keyboard = [
            [InlineKeyboardButton("🔮 ЗАДАТЬ ВОПРОС", callback_data="ask")],
            [InlineKeyboardButton("🃏 Послание дня", callback_data="daily_message"), InlineKeyboardButton("😴 Трактовка сна", callback_data="dream_menu")],
            [InlineKeyboardButton("👤 Профиль", callback_data="stats"), InlineKeyboardButton("🧠 Лучше к психологу", url="https://t.me/hypnotic_fire")],
            [InlineKeyboardButton("✨ Другие возможности", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.message.edit_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Сохраняем/получаем пользователя в БД
        referred_by = None
        if context.args and context.args[0].isdigit():
            referred_by = int(context.args[0])
            
        user_manager.get_or_create_user(user, referred_by=referred_by)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        message = update.message if update.message else update.callback_query.message
        help_text = f"""
📚 *Что я умею:*

*🔮 ГАДАНИЯ И ОТВЕТЫ:*
• /ask - Задать любой вопрос (Таро + И-Цзин + Астро)
• /horoscope - Гороскоп
• /dream - Трактовка сна

*🌟 АНАЛИЗ ЛИЧНОСТИ:*
• /natal - Натальная карта
• /numerology - Нумерология Сюцай
• /matrix - Матрица Судьбы

*❓ Как спрашивать:*
Просто напиши свой вопрос или запиши голосовое сообщение. Чем конкретнее вопрос, тем точнее ответ. ✨

*Поддержка:* @hypnotic_fire
"""
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu")]]
        await message.reply_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /ask"""
        self._reset_state(context)
        message = update.message if update.message else update.callback_query.message
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu")]]
        await message.reply_text(
            "🔮 Задай свой вопрос. Я внимательно слушаю...\n\n"
            "Можешь написать текстом или записать голосовое сообщение.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        # awaiting_question removed - any text message not handled by awaiting_data flows is treated as a question
    
        # Команда ritual удалена
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats - статистика пользователя"""
        user = update.effective_user
        db_user = user_manager.get_or_create_user(user)
        
        status = "💎 PREMIUM" if db_user.is_premium else "🆓 BASIC"
        energy_emoji = "⚡" if db_user.questions_today < settings.free_questions_per_day else "🪫"
        
        # Особый значок для премиум юзера
        badge = "✨🌟🌀" if db_user.is_premium else ""
        
        stats_text = f"""
{badge} 👤 *ПРОФИЛЬ: {user.first_name}* {badge}

✨ Статус: *{status}*
"""
        # Данные пользователя
        user_data = user_manager.get_user_data(user.id)
        if user_data:
            if user_data.birth_date:
                stats_text += f"📅 Дата рождения: *{user_data.birth_date.strftime('%d.%m.%Y')}*\n"
            if user_data.zodiac_sign:
                # Находим эмодзи
                sign_en = None
                for en, ru in horoscope_parser.SIGN_NAMES_RU.items():
                    if ru.lower() == user_data.zodiac_sign.lower():
                        sign_en = en
                        break
                emoji = horoscope_parser.SIGN_EMOJIS.get(sign_en, "✨")
                stats_text += f"♈ Знак: *{emoji} {user_data.zodiac_sign}*\n"
        
        stats_text += f"""
{energy_emoji} Энергии сегодня: *{db_user.questions_today}/{settings.free_questions_per_day}*
♾ Всего озарений: *{db_user.total_questions_asked}*
👥 Приглашено друзей: *{db_user.referral_count}*
✨ Бонусных озарений: *{db_user.bonus_questions}*
🃏 Раскладов Таро: *{db_user.tarot_today}/1*
"""
        if db_user.is_premium and db_user.premium_until:
             stats_text += f"📅 Активен до: *{db_user.premium_until.strftime('%d.%m.%Y')}*\n"
             
        stats_text += f"""
🔔 Рассылка: *{"✅ Активна" if db_user.daily_prediction_enabled else "❌ Отключена"}*

🔗 Твоя реферальная ссылка:
`https://t.me/{(await context.bot.get_me()).username}?start={user.id}`
"""
        keyboard = []
        if not db_user.is_premium:
            keyboard.append([InlineKeyboardButton("🚀 Стать PREMIUM", callback_data="premium")])
            
        keyboard.append([InlineKeyboardButton("🔔 Вкл/Выкл рассылку", callback_data="toggle_daily")])
        keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu")])
        
        message = update.message if hasattr(update, 'message') and update.message else update.callback_query.message
        if hasattr(update, 'callback_query') and update.callback_query:
            await message.edit_text(fix_markdown(stats_text), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await message.reply_text(fix_markdown(stats_text), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        logger.info(f"Handler: received message from {update.effective_user.id}: {update.message.text}")

        if await handle_awaiting_data(update, context):
            return
            
        # Обработка уточняющего вопроса
        if context.user_data.get('awaiting_followup'):
            await self.process_followup_question(update, context, update.message.text)
            return
        
        text = update.message.text
        if text and text.lower() in ['отмена', 'cancel', '/cancel']:
            self._reset_state(context)
            await update.message.reply_text("🧘 Путь очищен. Возвращаемся в начало.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В меню", callback_data="menu")]]))
            return

        await self.process_general_question(update, context, text)

    async def process_followup_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
        """Обработка уточняющего вопроса"""
        context.user_data['awaiting_followup'] = False
        user = update.effective_user
        
        count = context.user_data.get('followup_count', 0)
        
        # Лимит 2 уточнения
        if count >= 2:
            keyboard = [
                [InlineKeyboardButton("♾ Новый вопрос", callback_data="ask"), InlineKeyboardButton("🔙 В меню", callback_data="menu")]
            ]
            await update.message.reply_text(
                "✋ Я уже сказал всё, что должен был. Истина не в многословии, а в осознании сказанного.\n\n"
                "Перечитай мои ответы выше или задай совершенно новый вопрос.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        await update.message.reply_text("⏳ Источник углубляет ответ...")
        
        try:
            original_q = context.user_data.get('last_question', '')
            # Получаем ответ
            last_response = context.user_data.get('last_oracle_response', {})
            # Формируем контекст для AI (берем интерпретацию)
            context_data = {'previous_answer': last_response.get('interpretation', '')}
            
            answer = await oracle_interpreter.generate_followup_response(original_q, question, context_data)
            
            # Увеличиваем счетчик
            context.user_data['followup_count'] = count + 1
            
            keyboard = [
                [InlineKeyboardButton("🔍 Подробнее", callback_data="ask_details")] if count + 1 < 2 else [],
                [InlineKeyboardButton("♾ Новый вопрос", callback_data="ask"), InlineKeyboardButton("🔙 В меню", callback_data="menu")]
            ]
            # Убираем пустые списки
            keyboard = [k for k in keyboard if k]
            
            await update.message.reply_text(fix_markdown(answer), parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            logger.error(f"Error in followup: {e}")
            await update.message.reply_text("❌ Источник туманен сейчас. Попробуй позже.")

    async def process_general_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
        """Единая логика обработки вопроса (текст/голос)"""
        if not question or not question.strip():
            await update.message.reply_text("❓ Вопрос пуст. О чём хочешь спросить?")
            return
            
        user = update.effective_user
        
        # Гарантируем, что пользователь существует в БД перед проверкой лимитов
        try:
            user_manager.get_or_create_user(user)
        except Exception as e:
            logger.error(f"Failed to create user in DB: {e}")
            
        # Проверка лимитов с обработкой ошибок
        try:
            allowed, result = user_manager.check_and_update_limits(user.id, free_limit=settings.free_questions_per_day)
            
            if not allowed:
                keyboard = [[InlineKeyboardButton("💎 Купить Энергию", callback_data="premium")]]
                await update.message.reply_text(
                    f"🪫 *Энергия исчерпана*\n\n{result}\nПриходи завтра или получи безлимитный доступ.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return

            if isinstance(result, str) and result.startswith("bonus_"):
                bonus_left = result.split("_")[1]
                await update.message.reply_text(f"✨ Использовано бонусное озарение! (Осталось: {bonus_left})")
        except Exception as e:
            logger.error(f"Error checking limits: {e}")
            # В случае ошибки лимитов - пускаем (fail open) или блокируем? Лучше пустить, чтобы не блокировать юзера из-за бага
            logger.warning("Limit check failed, allowing request as fallback")


        processing_msg = await update.message.reply_text(
            "🙏 Обращаюсь к Источнику с твоим вопросом...\n"
            "Ожидай ответа. 🌌"
        )
        
        try:
            db_user = user_manager.get_or_create_user(user)
            logger.info(f"Processing question for user {user.id}: {question[:50]}...")
            
            oracle_response = await oracle_interpreter.process_question(question, user.first_name, is_premium=db_user.is_premium)
            
            if not oracle_response:
                raise ValueError("Oracle returned empty response")
            
            context.user_data['last_question'] = question
            context.user_data['last_oracle_response'] = oracle_response
            
            response_text = fix_markdown(oracle_response['interpretation'])
            
            await processing_msg.delete()
            await update.message.reply_text(response_text, parse_mode='Markdown')
            
            # Сохраняем в историю
            user_manager.save_question(user.id, question, oracle_response)
            
            # Сбрасываем счетчик уточнений
            context.user_data['followup_count'] = 0
            
            share_url = f"https://t.me/share/url?url=https://t.me/{(await context.bot.get_me()).username}?start={user.id}&text=🔮%20Этот%20Оракул%20видит%20всё.%20Спроси%20его%20и%20ты!"
            
            keyboard = [
                [
                    InlineKeyboardButton("👍 Полезно", callback_data="rate_good"),
                    InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")
                ],
                [InlineKeyboardButton("🔍 Детали расклада", callback_data="details")],
                [
                    InlineKeyboardButton("🧠 Лучше к психологу", url="https://t.me/hypnotic_fire"),
                    InlineKeyboardButton("♾ Новый вопрос", callback_data="ask")
                ],
                [
                    InlineKeyboardButton("🔙 В меню", callback_data="menu"),
                    InlineKeyboardButton("🚀 Поделиться", url=share_url)
                ]
            ]
            await update.message.reply_text(
                "Оцени ответ Источника: ✨", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            # Пытаемся отредактировать сообщение о процессинге, если оно осталось
            try:
                await processing_msg.edit_text(
                    "😔 Видение затуманено... Произошла ошибка. "
                    "Пожалуйста, попробуй позже или напиши в поддержку. 🛠"
                )
            except:
                # Если, например, processing_msg уже удалено
                await update.message.reply_text(
                    "😔 Ошибка обработки. Попробуйте еще раз."
                )

    

    async def natal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /natal - натальная карта"""
        self._reset_state(context)
        message = update.message if update.message else update.callback_query.message
        if 'user_info' in context.user_data and 'date_str' in context.user_data['user_info']:
            saved_date = context.user_data['user_info'].get('date_str')
            keyboard = [
                [InlineKeyboardButton(f"Использовать {saved_date}", callback_data="use_saved_natal")],
                [InlineKeyboardButton("Ввести новые данные", callback_data="new_natal")],
                [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
            ]
            await message.reply_text(
                f"🌟 *НАТАЛЬНАЯ КАРТА*\n\nУ меня сохранены данные: *{saved_date}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await message.reply_text(
                "🌟 *НАТАЛЬНАЯ КАРТА*\n\n"
                "Для расчета натальной карты мне нужна информация:\n"
                "• Дата рождения (дд.мм.гггг)\n"
                "• Время рождения (чч:мм)\n"
                "• Город рождения (широта/долгота или название)\n\n"
                "Пример: `15.03.1990 14:30 Москва`\n\n"
                "Отправь эти данные в следующем сообщении.",
                parse_mode='Markdown'
            )
            context.user_data['awaiting_natal_data'] = True
    
    async def numerology_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /numerology - нумерология Сюцай"""
        self._reset_state(context)
        message = update.message if update.message else update.callback_query.message
        if 'user_info' in context.user_data and 'date_str' in context.user_data['user_info']:
            saved_date = context.user_data['user_info'].get('date_str')
            keyboard = [
                [InlineKeyboardButton(f"Использовать {saved_date}", callback_data="use_saved_numerology")],
                [InlineKeyboardButton("Ввести новые данные", callback_data="new_numerology")],
                [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
            ]
            await message.reply_text(
                f"🔢 *НУМЕРОЛОГИЯ*\n\nСохраненная дата: *{saved_date}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await message.reply_text(
                "🔢 *КИТАЙСКАЯ НУМЕРОЛОГИЯ СЮЦАЙ*\n\n"
                "Для расчета ваших чисел судьбы введите дату рождения:\n"
                "Формат: `дд.мм.гггг`\n\n"
                "Пример: `15.03.1990`",
                parse_mode='Markdown'
            )
            context.user_data['awaiting_numerology_date'] = True
    
    
    async def matrix_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /matrix - матрица судьбы"""
        self._reset_state(context)
        message = update.message if update.message else update.callback_query.message
        if 'user_info' in context.user_data and 'date_str' in context.user_data['user_info']:
            saved_date = context.user_data['user_info'].get('date_str')
            keyboard = [
                [InlineKeyboardButton(f"Использовать {saved_date}", callback_data="use_saved_matrix")],
                [InlineKeyboardButton("Ввести новые данные", callback_data="new_matrix")],
                [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
            ]
            await message.reply_text(
                f"🔮 *МАТРИЦА СУДЬБЫ*\n\nСохраненная дата: *{saved_date}*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await message.reply_text(
                "🔮 *МАТРИЦА СУДЬБЫ*\n\n"
                "Для расчета матрицы судьбы введите дату рождения:\n"
                "Формат: `дд.мм.гггг`\n\n"
                "Пример: `15.03.1990`",
                parse_mode='Markdown'
            )
            context.user_data['awaiting_matrix_date'] = True
    
    async def horoscope_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /horoscope - выбор периода"""
        self._reset_state(context)
        message = update.message if update.message else update.callback_query.message
        
        keyboard = [
            [
                InlineKeyboardButton("📅 Сегодня", callback_data="period_today"),
                InlineKeyboardButton("📅 Завтра", callback_data="period_tomorrow")
            ],
            [
                InlineKeyboardButton("📅 Неделя", callback_data="period_week"),
                InlineKeyboardButton("📅 Месяц", callback_data="period_month")
            ],
            [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
        ]
        
        await message.reply_text(
            "⭐ *ГОРОСКОП*\n\nВыберите период прогноза:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def tarot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /tarot - расклад таро"""
        self._reset_state(context)
        await show_tarot_menu(update, context)

    async def compatibility_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /compatibility - совместимость"""
        message = update.message if update.message else update.callback_query.message
        self._reset_state(context)
        await message.reply_text(
            "💞 *СОВМЕСТИМОСТЬ*\n\nВведи две даты рождения через пробел.\nПример: `15.03.1990 20.01.1995`",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_compatibility_dates'] = True

    async def dream_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /dream - трактовка сна"""
        message = update.message if update.message else update.callback_query.message
        self._reset_state(context)
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu")]]
        await message.reply_text(
            "😴 *ТРАКТОВКА СНА*\n\nОпиши свой сон максимально подробно. Ты можешь написать текст или отправить голосовое сообщение. 🎙",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        context.user_data['awaiting_dream'] = True

    async def show_horoscope_signs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать выбор знаков зодиака"""
        query = update.callback_query
        
        # Определяем знак пользователя если есть
        user_sign_en = None
        user_sign_ru = None
        
        # Попытка получить данные из БД, если в контексте пусто
        user_info = context.user_data.get('user_info', {})
        if not user_info or 'birth_date' not in user_info:
            db_data = user_manager.get_user_data(update.effective_user.id)
            if db_data and db_data.birth_date:
                user_info['birth_date'] = db_data.birth_date
                context.user_data['user_info'] = user_info

        if 'birth_date' in user_info:
            bd = user_info['birth_date']
            user_sign_en = horoscope_parser.get_sign_from_date(bd.day, bd.month)
            user_sign_ru = horoscope_parser.SIGN_NAMES_RU.get(user_sign_en)

        keyboard = []
        
        # Если есть знак пользователя, добавляем его первым
        if user_sign_ru:
            emoji = horoscope_parser.SIGN_EMOJIS.get(user_sign_en, "✨")
            keyboard.append([InlineKeyboardButton(f"🌟 Твой знак: {emoji} {user_sign_ru}", callback_data=f"sign_{user_sign_ru.lower()}")])
            keyboard.append([InlineKeyboardButton("───────────────", callback_data="none")])

        # Общий список
        signs = [
            ("♈ Овен", "овен"), ("♉ Телец", "телец"), ("♊ Близнецы", "близнецы"),
            ("♋ Рак", "рак"), ("♌ Лев", "лев"), ("♍ Дева", "дева"),
            ("♎ Весы", "весы"), ("♏ Скорпион", "скорпион"), ("♐ Стрелец", "стрелец"),
            ("♑ Козерог", "козерог"), ("♒ Водолей", "водолей"), ("♓ Рыбы", "рыбы")
        ]
        
        for i in range(0, len(signs), 3):
            row = [InlineKeyboardButton(s[0], callback_data=f"sign_{s[1]}") for s in signs[i:i+3]]
            keyboard.append(row)
            
        keyboard.append([InlineKeyboardButton("🔙 К выбору периода", callback_data="horo_menu")])
        
        period = context.user_data.get('temp_horo_period', 'today')
        period_ru = {"today": "сегодня", "tomorrow": "завтра", "week": "неделю", "month": "месяц"}.get(period, period)
        
        await query.message.edit_text(
            f"⭐ *ГОРОСКОП на {period_ru.upper()}*\n\nВыберите знак зодиака:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def moon_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /moon - лунный календарь (сразу данные на сегодня)"""
        await self.show_moon_info(update, context, "today")

    async def show_moon_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, period: str):
        """Показать инфо о Луне для конкретного периода"""
        query = update.callback_query
        message = update.message if update.message else (query.message if query else None)
        
        if query:
            await query.edit_message_text(f"🌙 Запрашиваю данные у Луны на {period}...")
        else:
            processing_msg = await message.reply_text(f"🌙 Запрашиваю данные у Луны на {period}...")

        moon_info = await moon_parser.get_moon_info(period)
        
        keyboard = []
        if period == "today":
            keyboard.append([InlineKeyboardButton("📅 Завтра", callback_data="moon_tomorrow")])
        else:
             keyboard.append([InlineKeyboardButton("📅 Сегодня", callback_data="moon_today")])
        
        keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        if moon_info:
            formatted = moon_parser.format_moon_info(moon_info)
            if query:
                await query.edit_message_text(formatted, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await processing_msg.edit_text(formatted, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            err_text = "😔 Луна скрыта облаками (ошибка получения данных). Попробуйте позже."
            if query:
                await query.edit_message_text(err_text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await processing_msg.edit_text(err_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка голосовых сообщений"""
        processing_msg = await update.message.reply_text("🎤 Внимательно слушаю твой голос...")
        
        try:
            voice_file = await context.bot.get_file(update.message.voice.file_id)
            
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            await voice_file.download_to_drive(temp_file_path)
            
            await processing_msg.edit_text("🎤 Распознаю шепот Источника... ⚡")
            text = await voice_handler.transcribe_audio(temp_file_path)
            
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            if not text:
                await processing_msg.edit_text("😔 Тишина... Не удалось разобрать слова. Попробуй еще раз или напиши текстом. ⌨️")
                return
                
            await processing_msg.edit_text(f"🗣️ *Ты спросил:*\n_{text}_", parse_mode='Markdown')
            
            # Передаем текст в единый процессор
            await self.process_general_question(update, context, text)
            
        except Exception as e:
            logger.error(f"Error handling voice: {e}")
            await processing_msg.edit_text("❌ Туман сгустился... Ошибка обработки голоса. 🎙")
    
    def _reset_state(self, context: ContextTypes.DEFAULT_TYPE):
        """Сбросить все флаги ожидания"""
        keys = ['awaiting_followup', 'awaiting_natal_data', 'awaiting_numerology_date', 
                'awaiting_matrix_date', 'awaiting_compatibility_dates', 'awaiting_question',
                'awaiting_horoscope_sign', 'awaiting_dream']
        for key in keys:
            context.user_data[key] = False

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Callback answer failed: {e}")
        
        # Эти команды должны быть ПЕРВЫМИ, чтобы не попадать в startswith условия ниже
        if query.data == "menu":
            self._reset_state(context)
            keyboard = [
                [InlineKeyboardButton("🔮 Задать вопрос", callback_data="ask")],
                [InlineKeyboardButton("😴 Сны", callback_data="dream_menu"), InlineKeyboardButton("🌙 Лунный календарь", callback_data="moon")],
                [InlineKeyboardButton("⭐ Гороскоп", callback_data="horo_menu"), InlineKeyboardButton("🔢 Сюцай", callback_data="numerology_menu")],
                [InlineKeyboardButton("🔮 Матрица", callback_data="matrix_menu"), InlineKeyboardButton("🃏 Таро", callback_data="tarot_spread_menu")],
                [InlineKeyboardButton("💞 Совместимость", callback_data="compatibility_menu"), InlineKeyboardButton("👤 Данные", callback_data="stats")],
                [InlineKeyboardButton("🔙 Назад", callback_data="start_msg"), InlineKeyboardButton("❓ Помощь", callback_data="help")]
            ]
            await query.message.edit_text("🎴 *МЕНЮ ВОЗМОЖНОСТЕЙ:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return

        if query.data == "stats":
            self._reset_state(context)
            await self.stats_command(update, context)
            return

        if query.data == "help":
            self._reset_state(context)
            await self.help_command(update, context)
            return

        if query.data == "start_msg":
             self._reset_state(context)
             await self.start_command(update, context)
             return

        if query.data == "tarot_spread_menu":
            await show_tarot_menu(update, context)
            return

        if query.data.startswith("tarot_sphere_"):
            sphere = query.data.replace("tarot_sphere_", "")
            await process_tarot_spread(update, context, sphere)
            return

        if query.data == "moon":
            self._reset_state(context)
            await self.moon_command(update, context)
            return

        if query.data.startswith("moon_"):
            period = query.data.split("_")[1]
            await self.show_moon_info(update, context, period)
            return

        if query.data == "dream_menu":
            self._reset_state(context)
            await self.dream_command(update, context)
            return

        if query.data == "dream_detailed":
            await process_dream_detailed(update, context)
            return

        if query.data == "ask_details_dream":
            await query.message.reply_text("🗣 Отрази в вопросе ту деталь сна, которая не дает тебе покоя. Я помогу ее расшифровать...")
            context.user_data['awaiting_followup'] = True
            return

        if query.data.startswith("sphere_"):
            sphere = query.data.split("_")[1]
            user = update.effective_user
            db_user = user_manager.get_or_create_user(user)
            
            # Проверка на премиум для определенных сфер
            premium_spheres = ["love", "money", "purpose"]
            if sphere in premium_spheres and not db_user.is_premium:
                keyboard = [[InlineKeyboardButton("🚀 Купить Премиум", callback_data="premium")]]
                await query.message.reply_text(
                    "💎 *Эту сферу видит только Премиум*\n\nОна требует более тонкой настройки и глубокого анализа Источника. Подключи Премиум, чтобы открыть все грани своей судьбы.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
            
            # Получаем данные последнего расчета
            calc_type = context.user_data.get('last_calc_type')
            calc_data = context.user_data.get('last_calc_data')
            
            if not calc_type or not calc_data:
                keyboard = [
                    [InlineKeyboardButton("🔢 Сюцай", callback_data="numerology_menu"), InlineKeyboardButton("🔮 Матрица", callback_data="matrix_menu")],
                    [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
                ]
                await query.message.reply_text(
                    "⚠️ Данные расчета утеряны (сессия истекла). Чтобы получить разбор по сферам, сначала проведи расчет заново:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            await query.message.reply_text("🔮 Обращаюсь к Источнику за подробностями...")
            
            # Получаем интерпретацию
            # Для простоты передаем строковое представление данных
            data_str = str(calc_data)
            interpretation = await oracle_interpreter.get_sphere_interpretation(
                sphere, calc_type, data_str, user.first_name, db_user.is_premium
            )
            
            # Кнопки для выбора периода
            keyboard = [
                [
                    InlineKeyboardButton("📅 На неделю", callback_data=f"period_recommend_week_{sphere}"),
                    InlineKeyboardButton("📅 На месяц", callback_data=f"period_recommend_month_{sphere}")
                ],
                [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
            ]
            
            await query.message.reply_text(
                f"✨ *РАЗБОР СФЕРЫ: {sphere.upper()}*\n\n{fix_markdown(interpretation)}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return

        if query.data.startswith("period_recommend_"):
             parts = query.data.split("_")
             period = parts[2] # week/month
             sphere = parts[3] # health/career/etc
             
             user = update.effective_user
             db_user = user_manager.get_or_create_user(user)
             
             calc_type = context.user_data.get('last_calc_type')
             calc_data = context.user_data.get('last_calc_data')
             
             if not calc_type or not calc_data:
                 await query.message.reply_text("⚠️ Данные утеряны. Проведи расчет заново.")
                 return
                 
             await query.message.reply_text(f"⏳ Источник готовит прогноз на {period}...")
             
             # Вызываем AI для прогноза на период
             # Мы можем повторно использовать get_sphere_interpretation с небольшим дополнением в промпте
             # Или добавить новый метод. Для скорости добавим здесь.
             
             period_ru = "неделю" if period == "week" else "месяц"
             
             prompt_addon = f"\n\nВАЖНО: Дай рекомендации именно на предстоящий {period_ru}."
             
             data_str = str(calc_data)
             interpretation = await oracle_interpreter.get_sphere_interpretation(
                 sphere + prompt_addon, calc_type, data_str, user.first_name, db_user.is_premium
             )
             
             await query.message.reply_text(
                 f"📅 *ПРОГНОЗ НА {period_ru.upper()} ({sphere.upper()})*\n\n{fix_markdown(interpretation)}",
                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В меню", callback_data="menu")]]),
                 parse_mode='Markdown'
             )
             return

        if query.data == "ask":
            await self.ask_command(update, context)
            return

        # Обработка гороскопов
        if query.data.startswith("horo_") or query.data.startswith("sign_"):
            # Унифицированная обработка знаков (префиксы horo_ и sign_)
            sign = query.data.replace("horo_", "").replace("sign_", "")
            await handle_horoscope_callback(update, context, sign)
            return
        
        # Обработка оценок
        if query.data in ["rate_good", "rate_bad"]:
            is_good = query.data == "rate_good"
            
            if is_good:
                await query.answer("🙏 Благодарю за отклик!", show_alert=False)
                # Оставляем текст как есть, просто меняем кнопки
                action_keyboard = [
                    [InlineKeyboardButton("🗣 Новый вопрос", callback_data="ask")],
                    [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
                ]
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(action_keyboard))
            else:
                # НЕ заменяем текст, а отправляем дополнительное сообщение
                await query.answer("Принято", show_alert=False)
                # Убираем кнопки оценки
                action_keyboard = [
                    [InlineKeyboardButton("🗣 Новый вопрос", callback_data="ask")],
                    [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
                ]
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(action_keyboard))
                
                # Отправляем дополнительное сообщение с рекомендацией
                text = "Похоже, мой ответ не попал в цель.\n\nВ таких ситуациях лучше всего обратиться к профессиональному психологу за живой консультацией:"
                keyboard = [
                    [InlineKeyboardButton("🧠 Лучше к психологу", url="https://t.me/hypnotic_fire")],
                    [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
                ]
                await query.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            # Логирование
            logger.info(f"User {update.effective_user.id} rated: {query.data}")
            return

        # Обработка Послания Дня
        if query.data == "daily_message":
            await query.message.reply_text("🙏 Слушаю шепот дня...")
            
            # Проверка кэша (Карта дня одна на весь день)
            today_str = datetime.now().strftime("%Y-%m-%d")
            saved_date = context.user_data.get('daily_message_date')
            saved_message = context.user_data.get('daily_message_text')
            
            if saved_date == today_str and saved_message:
                message = fix_markdown(saved_message)
                # Небольшая задержка для имитации "вспоминания", но не обращения
            else:
                message = fix_markdown(await oracle_interpreter.get_daily_guidance())
                # Сохраняем
                context.user_data['daily_message_date'] = today_str
                context.user_data['daily_message_text'] = message
            
            # Сохраняем "фейковый" контекст для кнопки "Подробнее"
            context.user_data['last_question'] = "Каков совет на сегодня? (Послание дня)"
            context.user_data['last_oracle_response'] = {
                'interpretation': message,
                'iching': {'formatted': 'День без гексаграмм'},
                'tarot': {'formatted': 'Карта дня'},
                'horary': {'formatted': 'Астрология момента'}
            }
            
            # Кнопки
            keyboard = [
                [InlineKeyboardButton("🔮 Задать вопрос", callback_data="ask")],
                [InlineKeyboardButton("✨ Другие возможности", callback_data="menu")],
                [InlineKeyboardButton("🧠 Лучше к психологу", url="https://t.me/hypnotic_fire")]
            ]
            
            text = f"{message}\n\n🔮 *Есть вопрос? Задай его мне прямо сейчас...*"
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return



        if query.data == "buy_premium":
            # Отправка инвойса на Telegram Stars
            title = "Oracle Premium"
            description = "Безлимитный доступ к Источнику и продвинутые модели ИИ на 30 дней."
            payload = "premium_subscription"
            currency = "XTR" # Код для Telegram Stars
            price = 150
            prices = [LabeledPrice("Premium Access", price)]
            
            await context.bot.send_invoice(
                query.message.chat_id,
                title,
                description,
                payload,
                "",  # Provider token - пустой для Telegram Stars
                currency,
                prices
            )
            await query.answer()
            return

        # Обработка Послания Дня, Премиум и Deepen остается выше

        if query.data == "deepen":
            if 'last_oracle_response' in context.user_data:
                await query.message.reply_text("📜 Вглядываюсь в глубину...")
                
                question = context.user_data.get('last_question', '')
                oracle_response = context.user_data['last_oracle_response']
                
                # Генерируем уточнение
                deep_analysis = await oracle_interpreter.generate_followup_response(
                    question, 
                    "Раскрой детали подробнее. Что именно ты увидел в Источнике? Объясни образы.", 
                    oracle_response
                )
                
                await query.message.reply_text(fix_markdown(deep_analysis), parse_mode='Markdown')
            else:
                 await query.message.reply_text("⚠️ Контекст утерян. Задай новый вопрос.")
            return

        # Меню для модулей (чтобы кнопка Меню работала красиво)
        if query.data == "horo_menu":
             self._reset_state(context)
             await self.horoscope_command(update, context)
             return

        if query.data == "numerology_menu":
             self._reset_state(context)
             await self.numerology_command(update, context)
             return
             
        if query.data.startswith("period_"):
             period = query.data.split("_")[1]
             context.user_data['temp_horo_period'] = period
             
             # Проверяем, знаем ли мы знак пользователя
             user_info = context.user_data.get('user_info', {})
             user_sign_ru = None
             
             if not user_info or 'birth_date' not in user_info:
                 db_data = user_manager.get_user_data(update.effective_user.id)
                 if db_data and db_data.birth_date:
                     user_info['birth_date'] = db_data.birth_date
                     context.user_data['user_info'] = user_info
             
             if 'birth_date' in user_info:
                 bd = user_info['birth_date']
                 user_sign_en = horoscope_parser.get_sign_from_date(bd.day, bd.month)
                 user_sign_ru = horoscope_parser.SIGN_NAMES_RU.get(user_sign_en)
                 logger.info(f"Horoscope: Found birth_date {bd}, calculated sign: {user_sign_en} ({user_sign_ru})")
             
             if user_sign_ru:
                 # Если знак известен, сразу показываем гороскоп
                 await handle_horoscope_callback(update, context, user_sign_ru.lower())
             else:
                 # Иначе показываем выбор знаков
                 await self.show_horoscope_signs(update, context)
             return
             

        if query.data == "matrix_menu":
             self._reset_state(context)
             await self.matrix_command(update, context)
             return

        if query.data == "compatibility_menu":
             await self.compatibility_command(update, context)
             return
        
        # Обработка использования сохраненных данных
        if query.data == "use_saved_natal":
             info = context.user_data['user_info']
             # Формируем строку как будто ввел пользователь
             text = f"{info['date_str']} {info.get('time_str', '12:00')} {info.get('location', 'Москва')}"
             await process_natal_data(update, context, text)
             return
        if query.data == "new_natal":
             await query.message.reply_text("Введите дату, время и город рождения:")
             context.user_data['awaiting_natal_data'] = True
             return
             
        if query.data == "use_saved_numerology":
             text = context.user_data['user_info']['date_str']
             await process_numerology_date(update, context, text)
             return
        if query.data == "new_numerology":
             await query.message.reply_text("Введите дату рождения (дд.мм.гггг):")
             context.user_data['awaiting_numerology_date'] = True
             return

        if query.data == "use_saved_matrix":
             text = context.user_data['user_info']['date_str']
             await process_matrix_date(update, context, text)
             return
        if query.data == "new_matrix":
             await query.message.reply_text("Введите дату рождения (дд.мм.гггг):")
             context.user_data['awaiting_matrix_date'] = True
             return
        
        # Эти кнопки теперь обрабатываются в начале метода (menu, ask)
        
        
        # Блок ritual удален
        
        elif query.data == "details":
            if 'last_oracle_response' in context.user_data:
                oracle_response = context.user_data['last_oracle_response']
                
                details = f"""
📊 *Детали твоего гадания:*

{oracle_response['iching']['formatted']}

---

{oracle_response['tarot']['formatted']}

---

{oracle_response['horary']['formatted']}
"""
                keyboard = [
                    [InlineKeyboardButton("🔍 Уточнить", callback_data="ask_followup")],
                    [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
                ]
                await query.message.reply_text(
                    fix_markdown(details), 
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.message.reply_text("⚠️ Сначала задай вопрос!")
            return
        
        elif query.data == "ask_followup":
            await query.message.reply_text("🗣 Что именно ты хочешь уточнить? Напиши свой вопрос.")
            context.user_data['awaiting_followup'] = True
            return

        elif query.data == "toggle_daily":
            from database.database import SessionLocal
            from database.models import User
            session = SessionLocal()
            try:
                db_user = session.query(User).filter(User.telegram_id == query.from_user.id).first()
                if db_user:
                    db_user.daily_prediction_enabled = not db_user.daily_prediction_enabled
                    session.commit()
                    status = "включена" if db_user.daily_prediction_enabled else "выключена"
                    await query.answer(f"Рассылка {status}!", show_alert=True)
                    # Обновляем сообщение статов
                    await self.stats_command(update, context)
            finally:
                session.close()
            return



        # Обработка специальных кнопок завершена (stats, help и т.д. вынесены вверх)
    
    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /premium - покупка премиума"""
        message = update.message if update.message else update.callback_query.message
        
        text = """
💎 *ORACLE PREMIUM*

Открой полный доступ к мудрости Источника:
• ♾ Безлимитные вопросы
• 🧠 Доступ к продвинутой модели ИИ
• 🃏 Подробные разборы карт и знаков
• 🌅 Ежедневный утренний прогноз

Стоимость: *150 Telegram Stars* ⭐
"""
        keyboard = [
            [InlineKeyboardButton("💳 Купить за 150 ⭐", callback_data="buy_premium")],
            [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
        ]
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /referral"""
        user = update.effective_user
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={user.id}"
        
        text = f"""
👥 *Партнерская программа*

Приглашай друзей и получай бонусы!
За каждого приглашенного друга ты получаешь +5 озарений сегодня.

🔗 Твоя ссылка:
`{link}`
"""
        await update.message.reply_text(text, parse_mode='Markdown')

    async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка пре-чекаута"""
        query = update.pre_checkout_query
        # Проверяем payload
        if query.invoice_payload != 'premium_subscription':
            await query.answer(ok=False, error_message="Что-то пошло не так...")
        else:
            await query.answer(ok=True)

    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка успешного платежа"""
        user = update.effective_user
        user_manager.update_premium_status(user.id)
        
        await update.message.reply_text(
            "🎉 *Поздравляем!*\n\nТеперь ты обладаешь неограниченным доступом к Источнику. "
            "Твоё сознание расширено, а путь ясен. ✨",
            parse_mode='Markdown'
        )

    def _save_user(self, user):
        """Сохранить пользователя в БД"""
        user_manager.get_or_create_user(user)
    
    def run(self):
        """Запустить бота"""
        logger.info("Starting Oracle Bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


    async def set_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для админа: выдать премиум (для тестов)"""
        user = update.effective_user
        user_manager.update_premium_status(user.id)
        await update.message.reply_text("💎 Тестовый Премиум активирован! Проверь /stats")

def main():
    """Главная функция"""
    # Инициализация базы данных
    init_db()
    
    # --- DIAGNOSTIC STARTUP LOGGING ---
    logger.info("--- ORACLE BOT STARTUP DIAGNOSTICS ---")
    
    # Check Env Vars
    env_keys = ["TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY", "DATABASE_URL"]
    for key in env_keys:
        value = os.getenv(key)
        masked = f"{value[:4]}...{value[-4:]}" if value else "None"
        logger.info(f"ENV {key}: {masked}")
        
    logger.info("--------------------------------------")
    # ----------------------------------

    bot = OracleBot()
    bot.run()


if __name__ == "__main__":
    main()
