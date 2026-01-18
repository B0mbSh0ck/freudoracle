"""
Модуль парсинга гороскопов
Получение ежедневных гороскопов с различных сайтов
"""
import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime
import random


@dataclass
class Horoscope:
    """Гороскоп"""
    sign: str
    period: str  # today, tomorrow, week, month
    date: datetime
    general: str
    love: Optional[str] = None
    career: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None
    lucky_number: Optional[int] = None
    lucky_color: Optional[str] = None
    source: str = "horo.mail.ru"


class HoroscopeParser:
    """Парсер гороскопов"""
    
    ZODIAC_SIGNS = {
        'овен': 'aries',
        'телец': 'taurus',
        'близнецы': 'gemini',
        'рак': 'cancer',
        'лев': 'leo',
        'дева': 'virgo',
        'весы': 'libra',
        'скорпион': 'scorpio',
        'стрелец': 'sagittarius',
        'козерог': 'capricorn',
        'водолей': 'aquarius',
        'рыбы': 'pisces'
    }
    
    SIGN_NAMES_RU = {
        'aries': 'Овен',
        'taurus': 'Телец',
        'gemini': 'Близнецы',
        'cancer': 'Рак',
        'leo': 'Лев',
        'virgo': 'Дева',
        'libra': 'Весы',
        'scorpio': 'Скорпион',
        'sagittarius': 'Стрелец',
        'capricorn': 'Козерог',
        'aquarius': 'Водолей',
        'pisces': 'Рыбы'
    }

    SIGN_EMOJIS = {
        'aries': '♈',
        'taurus': '♉',
        'gemini': '♊',
        'cancer': '♋',
        'leo': '♌',
        'virgo': '♍',
        'libra': '♎',
        'scorpio': '♏',
        'sagittarius': '♐',
        'capricorn': '♑',
        'aquarius': '♒',
        'pisces': '♓'
    }
    
    def get_sign_from_date(self, day: int, month: int) -> str:
        """Определить знак зодиака по дню и месяцу"""
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "sagittarius"
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return "capricorn"
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "aquarius"
        else:
            return "pisces"
    
    # Запасные гороскопы если парсинг не сработает
    FALLBACK_HOROSCOPES = {
        'general': [
            "Сегодня звезды благоволят новым начинаниям. Используйте свою интуицию.",
            "День располагает к размышлениям и планированию. Избегайте поспешных решений.",
            "Отличный день для общения и новых знакомств. Ваше обаяние на высоте.",
            "Сосредоточьтесь на важных делах. Энергия способствует продуктивности.",
            "Время для отдыха и восстановления сил. Прислушайтесь к своему телу."
        ],
        'love': [
            "В отношениях возможны неожиданные повороты. Будьте открыты.",
            "Гармония и понимание с партнером. Хороший день для романтики.",
            "Возможны недопонимания. Проявите терпение и такт."
        ],
        'career': [
            "Профессиональные достижения на горизонте. Проявите инициативу.",
            "Сосредоточьтесь на деталях. Качество важнее количества.",
            "Хорошее время для сотрудничества и командной работы."
        ],
        'luck': [
            {'number': 7, 'color': 'золотой'},
            {'number': 3, 'color': 'синий'},
            {'number': 9, 'color': 'зеленый'},
            {'number': 5, 'color': 'красный'},
            {'number': 12, 'color': 'фиолетовый'}
        ]
    }
    
    async def get_horoscope(
        self,
        sign: str,
        period: str = 'today',
        use_fallback: bool = False
    ) -> Horoscope:
        """
        Получить гороскоп для знака зодиака
        
        Args:
            sign: Знак зодиака (русское или английское название)
            period: Период (today, tomorrow, week, month)
            use_fallback: Использовать резервные гороскопы
        """
        
        # Нормализуем знак
        sign_lower = sign.lower()
        sign_en = None

        if sign_lower in self.ZODIAC_SIGNS:
            sign_en = self.ZODIAC_SIGNS[sign_lower]
        elif sign_lower in self.SIGN_NAMES_RU:
            sign_en = sign_lower
        else:
            # Пробуем найти по русскому названию в SIGN_NAMES_RU (values)
            for en, ru in self.SIGN_NAMES_RU.items():
                if ru.lower() == sign_lower:
                    sign_en = en
                    break
        
        if not sign_en:
            # Если знак не распознан, используем fallback или возвращаем ошибку
            use_fallback = True
            sign_en = 'aries' # Fallback только для генерации текста если уж совсем никак
        
        sign_ru = self.SIGN_NAMES_RU.get(sign_en, sign)
        
        # Если используем fallback или парсинг не удался
        if use_fallback:
            return self._get_fallback_horoscope(sign_ru, period)
        
        # Пытаемся спарсить с сайта
        try:
            horoscope = await self._parse_horo_mail_ru(sign_en, period)
            if horoscope:
                return horoscope
        except Exception as e:
            print(f"Ошибка парсинга horo.mail.ru: {e}")
        
        # Если парсинг не удался, возвращаем fallback
        return self._get_fallback_horoscope(sign_ru, period)
    
    async def _parse_horo_mail_ru(self, sign: str, period: str) -> Optional[Horoscope]:
        """Парсинг с horo.mail.ru"""
        
        period_map = {
            'today': 'today',
            'tomorrow': 'tomorrow',
            'week': 'week',
            'month': 'month'
        }
        
        url_period = period_map.get(period, 'today')
        url = f"https://horo.mail.ru/prediction/{sign}/{url_period}/"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем текст гороскопа
                    # Структура сайта может меняться, поэтому это упрощенный парсинг
                    text_blocks = soup.find_all('p', class_='article__text')
                    
                    if not text_blocks:
                        # Пробуем альтернативный селектор
                        text_blocks = soup.find_all('div', class_='article__item__text')
                    
                    if text_blocks:
                        general_text = ' '.join([block.get_text(strip=True) for block in text_blocks[:2]])
                        
                        return Horoscope(
                            sign=self.SIGN_NAMES_RU.get(sign, sign),
                            period=period,
                            date=datetime.now(),
                            general=general_text,
                            source='horo.mail.ru'
                        )
        
        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
            return None
        
        return None
    
    def _get_fallback_horoscope(self, sign: str, period: str) -> Horoscope:
        """Получить резервный гороскоп"""
        
        luck = random.choice(self.FALLBACK_HOROSCOPES['luck'])
        
        period_text = {
            'today': 'Сегодня',
            'tomorrow': 'Завтра',
            'week': 'На этой неделе',
            'month': 'В этом месяце'
        }
        
        intro = period_text.get(period, 'Сегодня')
        
        general = f"{intro} {random.choice(self.FALLBACK_HOROSCOPES['general'])}"
        love = random.choice(self.FALLBACK_HOROSCOPES['love'])
        career = random.choice(self.FALLBACK_HOROSCOPES['career'])
        
        return Horoscope(
            sign=sign,
            period=period,
            date=datetime.now(),
            general=general,
            love=love,
            career=career,
            lucky_number=luck['number'],
            lucky_color=luck['color'],
            source='Oracle AI (generated)'
        )
    
    def format_horoscope(self, horoscope: Horoscope) -> str:
        """Форматировать гороскоп для отображения"""
        
        period_names = {
            'today': 'на сегодня',
            'tomorrow': 'на завтра',
            'week': 'на неделю',
            'month': 'на месяц'
        }
        
        period_text = period_names.get(horoscope.period, horoscope.period)
        
        # Находим эмодзи знака
        sign_key = 'aries'
        for en, ru in self.SIGN_NAMES_RU.items():
            if ru.lower() == horoscope.sign.lower():
                sign_key = en
                break
        
        emoji = self.SIGN_EMOJIS.get(sign_key, '✨')
        
        result = f"""
{emoji} **ГОРОСКОП ДЛЯ ЗНАКА {horoscope.sign.upper()}**
📅 {period_text.capitalize()}

**Общий прогноз:**
{horoscope.general}
"""
        
        if horoscope.love:
            result += f"\n💕 **Любовь:**\n{horoscope.love}\n"
        
        if horoscope.career:
            result += f"\n💼 **Карьера:**\n{horoscope.career}\n"
        
        if horoscope.health:
            result += f"\n🏥 **Здоровье:**\n{horoscope.health}\n"
        
        if horoscope.lucky_number or horoscope.lucky_color:
            result += "\n**🍀 Ваши счастливые символы:**\n"
            if horoscope.lucky_number:
                result += f"• Число: {horoscope.lucky_number}\n"
            if horoscope.lucky_color:
                result += f"• Цвет: {horoscope.lucky_color}\n"
        
        result += f"\n_Источник: {horoscope.source}_"
        
        return result.strip()


# Singleton
horoscope_parser = HoroscopeParser()
