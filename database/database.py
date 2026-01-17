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
    
    # Хак для миграции SQLite (добавление новых колонок если их нет)
    if "sqlite" in settings.database_url:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Проверяем наличие колонки bonus_questions в users
            res = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in res]
            if "bonus_questions" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN bonus_questions INTEGER DEFAULT 0"))
                conn.commit()
                print("✅ Миграция: добавлена колонка bonus_questions")
            
            if "last_tarot_date" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_tarot_date DATETIME"))
                conn.execute(text("ALTER TABLE users ADD COLUMN tarot_today INTEGER DEFAULT 0"))
                conn.commit()
                print("✅ Миграция: добавлены колонки для Таро")


def get_db():
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
