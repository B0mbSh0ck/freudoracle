"""
Настройка подключения к базе данных
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from database.models import Base

# Создаем engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug_mode,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Инициализировать базу данных (создать таблицы)"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
