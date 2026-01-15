"""
Скрипт инициализации проекта
Создает базу данных и необходимые директории
"""
import os
from loguru import logger
from database.database import init_db


def create_directories():
    """Создать необходимые директории"""
    directories = [
        'logs',
        'data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def main():
    """Главная функция инициализации"""
    logger.info("Starting project initialization...")
    
    # Создаем директории
    create_directories()
    
    # Инициализируем базу данных
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully!")
    
    logger.success("✅ Project initialization completed!")
    logger.info("Next steps:")
    logger.info("1. Copy .env.example to .env")
    logger.info("2. Fill in your API keys in .env file")
    logger.info("3. Run: python main.py")


if __name__ == "__main__":
    main()
