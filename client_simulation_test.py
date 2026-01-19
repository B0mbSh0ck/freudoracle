
import asyncio
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Мокаем зависимости до импорта бота
sys.modules['database.database'] = MagicMock()
sys.modules['database.models'] = MagicMock()
sys.modules['oracle.interpreter'] = MagicMock()
sys.modules['oracle.horoscope.horoscope_parser'] = MagicMock()
sys.modules['oracle.horoscope.moon_parser'] = MagicMock()
sys.modules['utils'] = MagicMock()
sys.modules['database.user_manager'] = MagicMock()
sys.modules['oracle.numerology.sucai'] = MagicMock()
sys.modules['oracle.matrix.destiny_matrix'] = MagicMock()
sys.modules['oracle.compatibility.compatibility'] = MagicMock()
sys.modules['oracle.natal.natal_chart'] = MagicMock()

# Теперь импортируем только то, что будем тестировать (логику обработчиков)
from main import OracleBot
from bot.extended_handlers import process_numerology_date, handle_awaiting_data

class BotClientSimulation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = OracleBot()
        self.update = MagicMock()
        self.context = MagicMock()
        self.context.user_data = {}
        self.update.effective_user.id = 12345
        self.update.effective_user.first_name = "TestUser"
        
        # Мокаем метод отправки сообщения
        self.send_msg = AsyncMock()
        self.update.message.reply_text = self.send_msg
        self.update.callback_query.message.reply_text = self.send_msg

    async def test_scenario_invalid_date_numerology(self):
        """ИТЕРАЦИЯ 1: Тест на ввод несуществующей даты (31.02)"""
        print("\n--- Тест: Несуществующая дата (31.02) ---")
        
        # Имитируем состояние ожидания даты
        self.context.user_data['awaiting_numerology_date'] = True
        
        # Клиент вводит некорректную дату
        self.update.message.text = "31.02.1990"
        
        # Вызываем обработчик
        processed = await handle_awaiting_data(self.update, self.context)
        
        # Проверяем результат
        self.assertTrue(processed)
        # Проверяем, что бот ответил вежливой ошибкой, а не упал
        args, kwargs = self.send_msg.call_args
        self.assertIn("Такой даты не существует", args[0])
        print("✅ Бот поймал ошибку даты и ответил пользователю.")

    async def test_scenario_empty_question(self):
        """ИТЕРАЦИЯ 2: Тест на пустой вопрос"""
        print("\n--- Тест: Пустой вопрос ---")
        
        self.update.message.text = "   " # Только пробелы
        
        await self.bot.handle_message(self.update, self.context)
        
        # Проверяем, что бот попросил ввести реальный текст
        args, kwargs = self.send_msg.call_args
        self.assertIn("Вопрос пуст", args[0])
        print("✅ Бот заблокировал пустой ввод.")

    async def test_scenario_cancel_command(self):
        """ИТЕРАЦИЯ 3: Тест команды /cancel"""
        print("\n--- Тест: Команда /cancel ---")
        
        # Устанавливаем любое состояние
        self.context.user_data['awaiting_question'] = True
        self.update.message.text = "/cancel"
        
        await self.bot.handle_message(self.update, self.context)
        
        # Проверяем, что состояние сброшено
        self.assertFalse(self.context.user_data.get('awaiting_question'))
        args, kwargs = self.send_msg.call_args
        self.assertIn("Путь очищен", args[0])
        print("✅ Команда /cancel успешно сбросила состояние.")

    async def test_scenario_session_expired(self):
        """ИТЕРАЦИЯ 4: Тест на протухшую сессию (нажатие кнопки из старого сообщения)"""
        print("\n--- Тест: Истекшая сессия ---")
        
        self.update.callback_query.data = "sphere_health"
        # user_data пуста (имитируем перезагрузку бота/истечение памяти)
        self.context.user_data = {} 
        
        await self.bot.button_handler(self.update, self.context)
        
        # Проверяем, что бот предложил восстановить расчет
        args, kwargs = self.send_msg.call_args
        self.assertIn("Данные расчета утеряны", args[0])
        self.assertIn("Сюцай", str(kwargs.get('reply_markup')))
        print("✅ Бот предложил восстановление сессии.")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
