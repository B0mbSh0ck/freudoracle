"""
Расширенные обработчики (Отключены при откате версий)
"""
from telegram import Update
from telegram.ext import ContextTypes

async def handle_awaiting_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Обработка ожидаемых данных от пользователя.
    В текущей версии (rollback) все расширенные функции отключены.
    Возвращает False, чтобы передать управление основному обработчику (Oracle).
    """
    return False

# Функции ниже отключены и удалены из кода для чистоты
