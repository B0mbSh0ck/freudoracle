"""
Главный файл Telegram бота Оракула
"""
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from loguru import logger
import sys
import os
import tempfile

from config.settings import settings
from oracle.interpreter import oracle_interpreter
from oracle.ritual.ritual_generator import ritual_generator
from database.models import User, QuestionSession
from database.database import SessionLocal
from utils import fix_markdown

# Импорт новых модулей
from bot.extended_handlers import (
    handle_awaiting_data,
    handle_horoscope_callback
)
from oracle.voice_handler import voice_handler

# Настройка логгирования
logger.remove()
logger.add(sys.stderr, level=settings.log_level)
logger.add("logs/bot.log", rotation="1 day", retention="7 days", level="INFO")


class OracleBot:
    """Telegram бот Оракула"""
    
    def __init__(self):
        self.app = Application.builder().token(settings.telegram_bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настроить обработчики команд и сообщений"""
        # Команды
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("ask", self.ask_command))
        self.app.add_handler(CommandHandler("ritual", self.ritual_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        
        # Новые команды
        self.app.add_handler(CommandHandler("natal", self.natal_command))
        self.app.add_handler(CommandHandler("numerology", self.numerology_command))
        self.app.add_handler(CommandHandler("matrix", self.matrix_command))
        self.app.add_handler(CommandHandler("horoscope", self.horoscope_command))
        
        # Callback кнопки
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Текстовые сообщения
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Голосовые сообщения
        self.app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        
        welcome_message = f"""
🔮 *Здравствуй, {user.first_name}.*

Я чувствую твой приход. Источник готов дать ответы.
Задай свой вопрос — текстом или голосом. Я здесь.
"""
        
        keyboard = [
            [InlineKeyboardButton("🔮 Задать вопрос", callback_data="ask")],
            [InlineKeyboardButton("🃏 Послание дня", callback_data="daily_message")],
            [InlineKeyboardButton("✨ Другие возможности", callback_data="menu")],
            [InlineKeyboardButton("🧠 Лучше к психологу", url="https://t.me/hypnotic_fire")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Сохраняем пользователя в БД
        self._save_user(user)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        message = update.message if update.message else update.callback_query.message
        help_text = f"""
📚 *Как пользоваться Оракулом:*

*🔮 ОСНОВНЫЕ  КОМАНДЫ:*
• /ask - Задать вопрос Оракулу
• /ritual - Получить персональный ритуал
• /stats - Твоя статистика

*🌟 АСТРОЛОГИЯ И НУМЕРОЛОГИЯ:*
• /natal - Натальная карта (дата, время, место рождения)
• /numerology - Китайская нумерология Сюцай
• /matrix - Матрица судьбы по 22 Арканам
• /horoscope - Ежедневный гороскоп

*📝 Как задать вопрос:*
• Формулируй конкретно
• Спрашивай о том, что действительно важно
• Пример: "Что мне нужно знать о моей карьере?"

*🆓 Тарифы:*
Бесплатно: {settings.free_questions_per_day} вопроса в день
💎 Премиум: Безлимит - {settings.premium_price_rub}₽/месяц

*Поддержка:* @oracle\\_support
"""
        await message.reply_text(help_text, parse_mode='Markdown')
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /ask"""
        message = update.message if update.message else update.callback_query.message
        await message.reply_text(
            "🔮 Задай свой вопрос. Я внимательно слушаю...\n\n"
            "Можешь написать текстом или записать голосовое сообщение."
        )
        # Устанавливаем состояние ожидания вопроса
        context.user_data['awaiting_question'] = True
    
    async def ritual_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /ritual - получить ритуал"""
        # Проверяем, есть ли предыдущий вопрос
        if 'last_oracle_response' not in context.user_data:
            await update.message.reply_text(
                "⚠️ Сначала задай вопрос Оракулу (/ask), "
                "а потом я смогу создать для тебя персональный ритуал."
            )
            return
        
        await update.message.reply_text("🧘 Создаю для тебя персональный ритуал... Это займет минуту.")
        
        try:
            question = context.user_data.get('last_question', '')
            oracle_response = context.user_data['last_oracle_response']
            
            ritual = await ritual_generator.generate_ritual(question, oracle_response)
            
            await update.message.reply_text(fix_markdown(ritual), parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error generating ritual: {e}")
            await update.message.reply_text(
                "😔 Произошла ошибка при создании ритуала. Попробуй позже."
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats - статистика пользователя"""
        user = update.effective_user
        
        # В упрощенной версии - заглушка
        stats_text = f"""
📊 *Твоя статистика, {user.first_name}:*

Вопросов задано сегодня: 0/{settings.free_questions_per_day}
Всего вопросов: 0
Ритуалов получено: 0

Статус: 🆓 Бесплатный тариф

Хочешь безлимит? Команда /premium
"""
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        
        # Сначала проверяем, ожидаем ли мы какие-то данные
        if await handle_awaiting_data(update, context):
            return  # Данные обработаны, выходим
        
        question = update.message.text
        user = update.effective_user
        
        # Проверяем лимиты (упрощенная версия)
        # В продакшене здесь будет проверка БД
        
        # Отправляем сообщение о том, что обрабатываем вопрос
        processing_msg = await update.message.reply_text(
            "🙏 Обращаюсь к Источнику с твоим вопросом...\n"
            "Ожидай ответа."
        )
        
        try:
            # Обрабатываем вопрос через оракула
            oracle_response = await oracle_interpreter.process_question(question, user.first_name)
            
            # Сохраняем в контекст для возможных уточнений
            context.user_data['last_question'] = question
            context.user_data['last_oracle_response'] = oracle_response
            
            # Формируем ответ
            # Формируем ответ (только интерпретация, без технических деталей)
            response_text = fix_markdown(oracle_response['interpretation'])
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Отправляем ответ
            await update.message.reply_text(response_text, parse_mode='Markdown')
            
            # Кнопки для оценки и дальнейших действий
            keyboard = [
                [
                    InlineKeyboardButton("👍 Полезно", callback_data="rate_good"),
                    InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")
                ],
                [
                    InlineKeyboardButton("🧠 Лучше к психологу", url="https://t.me/hypnotic_fire"),
                    InlineKeyboardButton("🔍 Детали", callback_data="details")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Оцените ответ:", 
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            await processing_msg.edit_text(
                "😔 Произошла ошибка при обработке вопроса. "
                "Пожалуйста, попробуй позже или обратись в поддержку."
            )
    
    async def natal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /natal - натальная карта"""
        message = update.message if update.message else update.callback_query.message
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
        message = update.message if update.message else update.callback_query.message
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
        message = update.message if update.message else update.callback_query.message
        await message.reply_text(
            "🔮 *МАТРИЦА СУДЬБЫ*\n\n"
            "Для расчета матрицы судьбы введите дату рождения:\n"
            "Формат: `дд.мм.гггг`\n\n"
            "Пример: `15.03.1990`",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_matrix_date'] = True
    
    async def horoscope_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /horoscope - гороскоп"""
        message = update.message if update.message else update.callback_query.message
        keyboard = [
            [
                InlineKeyboardButton("♈ Овен", callback_data="horo_овен"),
                InlineKeyboardButton("♉ Телец", callback_data="horo_телец"),
                InlineKeyboardButton("♊ Близнецы", callback_data="horo_близнецы")
            ],
            [
                InlineKeyboardButton("♋ Рак", callback_data="horo_рак"),
                InlineKeyboardButton("♌ Лев", callback_data="horo_лев"),
                InlineKeyboardButton("♍ Дева", callback_data="horo_дева")
            ],
            [
                InlineKeyboardButton("♎ Весы", callback_data="horo_весы"),
                InlineKeyboardButton("♏ Скорпион", callback_data="horo_скорпион"),
                InlineKeyboardButton("♐ Стрелец", callback_data="horo_стрелец")
            ],
            [
                InlineKeyboardButton("♑ Козерог", callback_data="horo_козерог"),
                InlineKeyboardButton("♒ Водолей", callback_data="horo_водолей"),
                InlineKeyboardButton("♓ Рыбы", callback_data="horo_рыбы")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            "⭐ *ГОРОСКОП*\n\nВыберите ваш знак зодиака:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка голосовых сообщений"""
        # Сообщаем что "слушаем"
        processing_msg = await update.message.reply_text("🎤 Слушаю ваш вопрос...")
        
        try:
            # Получаем файл
            voice_file = await context.bot.get_file(update.message.voice.file_id)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            # Скачиваем файл
            await voice_file.download_to_drive(temp_file_path)
            
            # Транскрибируем
            await processing_msg.edit_text("🎤 Распознаю речь...")
            text = await voice_handler.transcribe_audio(temp_file_path)
            
            # Удаляем временный файл
            os.remove(temp_file_path)
            
            if not text:
                await processing_msg.edit_text("😔 Не удалось разобрать слова. Попробуйте написать текстом или записать снова.")
                return
                
            # Показываем распознанный текст
            await processing_msg.edit_text(f"🗣️ *Вы спросили:*\n_{text}_\n\n🔮 Гадаю...", parse_mode='Markdown')
            
            # Подменяем текст сообщения и вызываем обработчик текста
            # Создаем "фейковый" апдейт с текстом вместо голоса
            update.message.text = text
            
            # Вызываем стандартную обработку вопроса
            # Важно: используем метод _oracle_process_question или логику из handle_message
            # Но проще просто вызвать основной метод обработки, если бы он был отдельным
            
            # В нашем случае handle_message сам берет update.message.text
            # Мы его только что установили вручную!
            
            await self.handle_message(update, context)
            
            # ВАЖНО: handle_message сам отправит ответ. 
            # Но у нас остался processing_msg с текстом "Гадаю...", который handle_message заменит своим processing_msg/ответом
            # Это нормально.
            
        except Exception as e:
            logger.error(f"Error handling voice: {e}")
            await processing_msg.edit_text("❌ Произошла ошибка при обработке голосового сообщения.")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        # Обработка гороскопов
        if query.data.startswith("horo_"):
            sign = query.data.replace("horo_", "")
            await handle_horoscope_callback(update, context, sign)
            return
        
        # Обработка оценок
        if query.data in ["rate_good", "rate_bad"]:
            is_good = query.data == "rate_good"
            text = "🙏 Благодарю за отклик." if is_good else "🙏 Принято. Буду точнее."
            
            # Клавиатура действий после оценки
            action_keyboard = [
                [InlineKeyboardButton("📜 Узнать подробнее", callback_data="deepen")],
                [InlineKeyboardButton("🗣 Новый вопрос", callback_data="ask")],
                [InlineKeyboardButton("📋 Меню", callback_data="menu")]
            ]
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(action_keyboard)
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
            
            # Кнопки оценки
            keyboard = [
                [
                    InlineKeyboardButton("👍 Полезно", callback_data="rate_good"),
                    InlineKeyboardButton("👎 Не помогло", callback_data="rate_bad")
                ],
                [
                    InlineKeyboardButton("🧠 Лучше к психологу", url="https://t.me/hypnotic_fire"),
                    InlineKeyboardButton("📋 Меню", callback_data="menu")
                ]
            ]
            
            await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return

        # Обработка меню
        if query.data == "menu":
            keyboard = [
                [InlineKeyboardButton("⭐ Гороскоп", callback_data="horo_menu"), InlineKeyboardButton("🔢 Сюцай", callback_data="numerology_menu")],
                [InlineKeyboardButton("🔮 Матрица", callback_data="matrix_menu"), InlineKeyboardButton("🧘 Ритуал", callback_data="ritual")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")]
            ]
            await query.message.reply_text("🎴 *Меню Оракула:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            return

        # Обработка "Подробнее" (deepen)
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
             await self.horoscope_command(update, context)
             return
        if query.data == "numerology_menu":
             await self.numerology_command(update, context)
             return
        if query.data == "matrix_menu":
             await self.matrix_command(update, context)
             return
        
        if query.data == "ask":
            await query.message.reply_text(
                "🔮 Задай свой вопрос. Я внимательно слушаю..."
            )
        
        elif query.data == "ritual":
            # Перенаправляем на команду ritual
            if 'last_oracle_response' in context.user_data:
                await query.message.reply_text("🧘 Создаю для тебя персональный ритуал...")
                
                question = context.user_data.get('last_question', '')
                oracle_response = context.user_data['last_oracle_response']
                
                ritual = await ritual_generator.generate_ritual(question, oracle_response)
                await query.message.reply_text(fix_markdown(ritual), parse_mode='Markdown')
            else:
                await query.message.reply_text(
                    "⚠️ Сначала задай вопрос Оракулу!"
                )
        
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
                await query.message.reply_text(fix_markdown(details), parse_mode='Markdown')
            else:
                await query.message.reply_text("⚠️ Сначала задай вопрос!")
        
        elif query.data == "help":
            await self.help_command(query, context)
    
    def _save_user(self, user):
        """Сохранить пользователя в БД (заглушка)"""
        # TODO: Реализовать сохранение в БД
        logger.info(f"User {user.id} ({user.first_name}) started the bot")
    
    def run(self):
        """Запустить бота"""
        logger.info("Starting Oracle Bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Главная функция"""
    bot = OracleBot()
    bot.run()


if __name__ == "__main__":
    main()
