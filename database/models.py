"""
Модели базы данных
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    
    # Лимиты и статистика
    questions_today = Column(Integer, default=0)
    last_question_date = Column(DateTime, default=datetime.utcnow)
    total_questions_asked = Column(Integer, default=0)
    
    # Реферальная система
    referred_by = Column(Integer, nullable=True)
    referral_count = Column(Integer, default=0)
    
    # Настройки
    daily_prediction_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = relationship("QuestionSession", back_populates="user")
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class QuestionSession(Base):
    """Сессия вопроса к Оракулу"""
    __tablename__ = 'question_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Результаты гадания
    iching_hexagram_primary = Column(Integer, nullable=True)
    iching_hexagram_secondary = Column(Integer, nullable=True)
    tarot_card = Column(String(100), nullable=True)
    tarot_reversed = Column(Boolean, default=False)
    horary_ascendant = Column(String(50), nullable=True)
    
    # AI интерпретация
    interpretation = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="questions")
    followups = relationship("FollowUpQuestion", back_populates="session")
    
    def __repr__(self):
        return f"<QuestionSession(id={self.id}, user_id={self.user_id})>"


class FollowUpQuestion(Base):
    """Уточняющий вопрос"""
    __tablename__ = 'followup_questions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('question_sessions.id'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("QuestionSession", back_populates="followups")
    
    def __repr__(self):
        return f"<FollowUpQuestion(id={self.id}, session_id={self.session_id})>"


class UserData(Base):
    """Дополнительные данные пользователя (дата рождения и т.д.)"""
    __tablename__ = 'user_details'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    birth_date = Column(DateTime, nullable=True)
    birth_time = Column(String(10), nullable=True)
    birth_location = Column(String(255), nullable=True)
    zodiac_sign = Column(String(50), nullable=True)
    
    user = relationship("User", backref="details")


class Payment(Base):
    """Платежи (для будущей монетизации)"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=False)  # в копейках или звездах
    currency = Column(String(10), default='XTR')  # XTR для звезд
    status = Column(String(50), default='pending')  # pending, completed, failed
    payment_type = Column(String(50), default='stars')  # stars, card
    payment_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount})>"
