"""
Модуль для получения лунного календаря
"""
import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MoonInfo:
    """Информация о Луне"""
    lunar_day: str
    phase: str
    sign: str
    description: str
    recommendations: str

class MoonParser:
    """Парсер лунного календаря"""
    
    async def get_moon_info(self) -> Optional[MoonInfo]:
        """Получить информацию о Луне на сегодня"""
        url = "https://horo.mail.ru/moon/"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Парсинг horo.mail.ru/moon/
                    # Состояние Луны обычно в блоках article__text или подобных
                    
                    day_block = soup.find('div', class_='moon__info-day')
                    lunar_day = day_block.get_text(strip=True) if day_block else "Неизвестно"
                    
                    phase_block = soup.find('div', class_='moon__info-phase')
                    phase = phase_block.get_text(strip=True) if phase_block else "Неизвестно"
                    
                    sign_block = soup.find('div', class_='moon__info-sign')
                    sign = sign_block.get_text(strip=True) if sign_block else "Неизвестно"
                    
                    # Текстовое описание
                    text_blocks = soup.find_all('p', class_='article__text')
                    if not text_blocks:
                         text_blocks = soup.find_all('div', class_='article__item__text')
                         
                    description = ""
                    recommendations = ""
                    
                    if text_blocks:
                        description = text_blocks[0].get_text(strip=True)
                        if len(text_blocks) > 1:
                            recommendations = ' '.join([b.get_text(strip=True) for b in text_blocks[1:3]])
                    
                    return MoonInfo(
                        lunar_day=lunar_day,
                        phase=phase,
                        sign=sign,
                        description=description,
                        recommendations=recommendations
                    )
                    
        except Exception as e:
            print(f"Ошибка при получении лунного календаря: {e}")
            return None

    def format_moon_info(self, moon: MoonInfo) -> str:
        """Форматировать информацию о Луне для Telegram"""
        return f"""
🌙 *ЛУННЫЙ КАЛЕНДАРЬ НА СЕГОДНЯ*

🗓 *{moon.lunar_day}*
🌕 Фаза: *{moon.phase}*
♈ Луна в знаке: *{moon.sign}*

📖 *Общее влияние:*
{moon.description}

💡 *Рекомендации:*
{moon.recommendations}

_Источник: horo.mail.ru_
"""

moon_parser = MoonParser()
