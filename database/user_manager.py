
from datetime import datetime, date
from sqlalchemy.orm import Session
from database.models import User, QuestionSession, Payment, UserData
from database.database import SessionLocal

class UserManager:
    @staticmethod
    def get_or_create_user(tg_user, referred_by=None):
        session = SessionLocal()
        try:
            db_user = session.query(User).filter(User.telegram_id == tg_user.id).first()
            if not db_user:
                db_user = User(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    referred_by=referred_by
                )
                session.add(db_user)
                if referred_by:
                    referrer = session.query(User).filter(User.telegram_id == referred_by).first()
                    if referrer:
                        referrer.referral_count += 1
                session.commit()
                session.refresh(db_user)
            return db_user
        finally:
            session.close()

    @staticmethod
    def check_and_update_limits(telegram_id, free_limit=2):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False, "Пользователь не найден"

            # Сброс счетчика, если наступил новый день
            today = date.today()
            if user.last_question_date.date() < today:
                user.questions_today = 0
                user.last_question_date = datetime.utcnow()

            if user.is_premium:
                # У премиум пользователей нет лимитов или они другие
                user.questions_today += 1
                user.total_questions_asked += 1
                session.commit()
                return True, user.questions_today

            if user.questions_today >= free_limit:
                return False, "Лимит бесплатных вопросов на сегодня исчерпан."

            user.questions_today += 1
            user.total_questions_asked += 1
            user.last_question_date = datetime.utcnow()
            session.commit()
            return True, user.questions_today
        finally:
            session.close()

    @staticmethod
    def save_question(telegram_id, question_text, response_data):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return
            
            new_session = QuestionSession(
                user_id=user.id,
                question=question_text,
                interpretation=response_data.get('interpretation'),
                iching_hexagram_primary=response_data.get('iching', {}).get('primary', {}).get('number'),
                tarot_card=response_data.get('tarot', {}).get('card', {}).get('name')
            )
            session.add(new_session)
            session.commit()
        finally:
            session.close()

    @staticmethod
    def update_premium_status(telegram_id, days=30):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.is_premium = True
                # Устанавливаем дату окончания
                from datetime import timedelta
                user.premium_until = datetime.utcnow() + timedelta(days=days)
                session.commit()
        finally:
            session.close()

    @staticmethod
    def save_user_data(telegram_id, birth_date=None, birth_time=None, birth_location=None, zodiac_sign=None):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return
            
            data = session.query(UserData).filter(UserData.user_id == user.id).first()
            if not data:
                data = UserData(user_id=user.id)
                session.add(data)
            
            if birth_date:
                data.birth_date = birth_date
            if birth_time:
                data.birth_time = birth_time
            if birth_location:
                data.birth_location = birth_location
            if zodiac_sign:
                data.zodiac_sign = zodiac_sign
                
            session.commit()
        finally:
            session.close()

    @staticmethod
    def get_user_data(telegram_id):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return None
            
            data = session.query(UserData).filter(UserData.user_id == user.id).first()
            return data
        finally:
            session.close()

user_manager = UserManager()
