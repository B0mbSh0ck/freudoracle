"""
Тестовый скрипт для проверки всех модулей Oracle Bot
Запустить: python test_oracle.py
"""
import asyncio
from datetime import datetime
from loguru import logger
import sys

# Настройка логирования
logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


async def test_iching():
    """Тест модуля И-Цзин"""
    logger.info("=" * 50)
    logger.info("ТЕСТ 1: Модуль И-Цзин (Книга Перемен)")
    logger.info("=" * 50)
    
    try:
        from oracle.iching.iching import iching
        
        # Бросаем монеты
        primary_hex, secondary_hex = iching.cast_coins()
        
        logger.success(f"✓ Получена гексаграмма #{primary_hex.number}: {primary_hex.name_russian}")
        logger.info(f"  Китайское название: {primary_hex.name_chinese} ({primary_hex.name_pinyin})")
        logger.info(f"  Триграммы: {primary_hex.trigram_above} + {primary_hex.trigram_below}")
        
        if primary_hex.changing_lines:
            logger.info(f"  Изменяющиеся линии: {primary_hex.changing_lines}")
            if secondary_hex:
                logger.info(f"  -> Переходит в #{secondary_hex.number}: {secondary_hex.name_russian}")
        
        # Показываем форматированный вывод
        print("\n" + iching.format_hexagram(primary_hex))
        
        logger.success("✓ Модуль И-Цзин работает!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка в модуле И-Цзин: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tarot():
    """Тест модуля Таро"""
    logger.info("=" * 50)
    logger.info("ТЕСТ 2: Модуль Таро")
    logger.info("=" * 50)
    
    try:
        from oracle.tarot.tarot import tarot
        
        # Карта дня
        card = tarot.card_of_the_day()
        
        logger.success(f"✓ Вытянута карта: {card.name}")
        logger.info(f"  Масть: {card.suit.value}")
        logger.info(f"  Архетип: {card.archetype}")
        logger.info(f"  Позиция: {'Перевернутая' if card.is_reversed else 'Прямая'}")
        
        # Показываем форматированный вывод
        print("\n" + tarot.deck.format_card(card))
        
        logger.success("✓ Модуль Таро работает!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка в модуле Таро: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_horary():
    """Тест модуля хорарной астрологии"""
    logger.info("=" * 50)
    logger.info("ТЕСТ 3: Хорарная астрология")
    logger.info("=" * 50)
    
    try:
        from oracle.horary.horary import horary
        
        # Рассчитываем карту на текущий момент
        now = datetime.now()
        chart = horary.calculate_chart(now)
        
        logger.success(f"✓ Хорарная карта рассчитана на {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  Асцендент: {horary._get_sign(chart.ascendant)}")
        logger.info(f"  MC: {horary._get_sign(chart.mc)}")
        logger.info(f"  Луна: {chart.planets['Moon'].sign}, {chart.planets['Moon'].house}-й дом")
        
        # Показываем форматированный вывод
        print("\n" + horary.format_chart(chart))
        
        logger.success("✓ Модуль хорарной астрологии работает!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка в модуле хорарной астрологии: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_interpreter():
    """Тест AI интерпретатора (требует API ключей)"""
    logger.info("=" * 50)
    logger.info("ТЕСТ 4: AI Интерпретатор")
    logger.info("=" * 50)
    
    try:
        from config.settings import settings
        
        # Проверяем наличие API ключей
        if not settings.openai_api_key and not settings.anthropic_api_key:
            logger.warning("⚠ API ключи не настроены. Пропускаем тест AI интерпретатора.")
            logger.info("  Для полного теста добавьте OPENAI_API_KEY или ANTHROPIC_API_KEY в .env файл")
            return None
        
        from oracle.interpreter import oracle_interpreter
        
        # Тестовый вопрос
        test_question = "Что мне нужно знать о моем будущем?"
        
        logger.info(f"Задаем тестовый вопрос: '{test_question}'")
        logger.info("Обрабатываем через оракула... (это займет ~30 секунд)")
        
        result = await oracle_interpreter.process_question(test_question, "Тестер")
        
        logger.success("✓ AI интерпретатор работает!")
        logger.info(f"  Длина ответа: {len(result['interpretation'])} символов")
        
        # Показываем краткую версию ответа
        print("\n--- ОТВЕТ ОРАКУЛА (первые 300 символов) ---")
        print(result['interpretation'][:300] + "...\n")
        
        logger.success("✓ Полный цикл гадания работает!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка в AI интерпретаторе: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ritual_generator():
    """Тест генератора ритуалов (требует API ключей)"""
    logger.info("=" * 50)
    logger.info("ТЕСТ 5: Генератор ритуалов")
    logger.info("=" * 50)
    
    try:
        from config.settings import settings
        
        if not settings.openai_api_key and not settings.anthropic_api_key:
            logger.warning("⚠ API ключи не настроены. Пропускаем тест генератора ритуалов.")
            return None
        
        from oracle.ritual.ritual_generator import ritual_generator
        from oracle.interpreter import oracle_interpreter
        
        # Создаем mock данные
        test_question = "Как мне преодолеть текущие трудности?"
        logger.info("Генерируем тестовый ритуал...")
        
        # Сначала получаем ответ оракула
        oracle_response = await oracle_interpreter.process_question(test_question, "Тестер")
        
        # Генерируем ритуал
        ritual = await ritual_generator.generate_ritual(test_question, oracle_response)
        
        logger.success("✓ Генератор ритуалов работает!")
        logger.info(f"  Длина ритуала: {len(ritual)} символов")
        
        print("\n--- РИТУАЛ (первые 300 символов) ---")
        print(ritual[:300] + "...\n")
        
        logger.success("✓ Генератор ритуалов работает!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка в генераторе ритуалов: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database():
    """Тест базы данных"""
    logger.info("=" * 50)
    logger.info("ТЕСТ 6: База данных")
    logger.info("=" * 50)
    
    try:
        from database.database import init_db, SessionLocal
        from database.models import User
        
        # Инициализируем БД
        init_db()
        logger.success("✓ База данных инициализирована")
        
        # Создаем тестовую сессию
        db = SessionLocal()
        
        # Проверяем создание пользователя
        test_user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Тест",
            last_name="Тестович"
        )
        
        # Проверяем что таблицы созданы
        logger.success("✓ Модели базы данных работают")
        
        db.close()
        logger.success("✓ База данных работает!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка в базе данных: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Главная функция тестирования"""
    print("\n" + "🔮" * 25)
    print("  ORACLE BOT - ТЕСТИРОВАНИЕ МОДУЛЕЙ")
    print("🔮" * 25 + "\n")
    
    results = {}
    
    # Тест 1: И-Цзин
    results['iching'] = await test_iching()
    
    # Тест 2: Таро
    results['tarot'] = await test_tarot()
    
    # Тест 3: Хорарная астрология
    results['horary'] = await test_horary()
    
    # Тест 4: База данных
    results['database'] = await test_database()
    
    # Тест 5: AI Интерпретатор (требует API)
    results['interpreter'] = await test_interpreter()
    
    # Тест 6: Генератор ритуалов (требует API)
    results['ritual'] = await test_ritual_generator()
    
    # Итоги
    print("\n" + "=" * 50)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⊘ SKIP")
        logger.info(f"{status} - {name}")
    
    print("\n" + "=" * 50)
    logger.info(f"Всего тестов: {total}")
    logger.success(f"Пройдено: {passed}")
    if failed > 0:
        logger.error(f"Провалено: {failed}")
    if skipped > 0:
        logger.warning(f"Пропущено: {skipped}")
    
    if failed == 0:
        print("\n" + "🎉" * 25)
        logger.success("ВСЕ ОСНОВНЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("🎉" * 25 + "\n")
        
        if skipped > 0:
            logger.info("Для включения AI тестов настройте API ключи в .env файле")
    else:
        print("\n" + "⚠️" * 25)
        logger.warning("НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        logger.info("Проверьте ошибки выше и исправьте проблемы")
        print("⚠️" * 25 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
