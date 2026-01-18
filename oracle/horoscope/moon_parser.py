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
    
    async def get_moon_info(self, date_str: str = None) -> Optional[MoonInfo]:
        """
        Получить информацию о Луне.
        date_str: формат 'YYYY-MM-DD' для конкретной даты
        """
        # Базовый URL. horo.mail.ru/moon/ обычно редиректит на актуальную страницу
        url = "https://horo.mail.ru/moon/"
        if date_str:
            url = f"{url}{date_str}/"
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        # Попробуем альтернативный URL если основной не сработал
                        if not date_str:
                            url = "https://horo.mail.ru/moon-calendar/"
                            async with session.get(url, timeout=10) as resp2:
                                if resp2.status == 200:
                                    html = await resp2.text()
                                else:
                                    return None
                        else:
                            return None
                    else:
                        html = await response.text()
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем данные более гибко (по ключевым словам)
                    lunar_day = "Неизвестно"
                    phase = "Неизвестно"
                    sign = "Неизвестно"
                    description = ""
                    recommendations = ""

                    # Пытаемся найти специфические блоки или текст
                    # Лунный день обычно содержит "лунный день" или "лунные сутки"
                    day_elem = soup.find(lambda tag: tag.name in ['div', 'p', 'b'] and ("лунный день" in tag.text.lower() or "лунные сутки" in tag.text.lower()))
                    if day_elem:
                        lunar_day = day_elem.get_text(strip=True)[:100] # Ограничим длину

                    # Фаза
                    phase_elem = soup.find(lambda tag: tag.name in ['div', 'p', 'b'] and any(p in tag.text.lower() for p in ["фаза", "луна растет", "луна убывает", "новолуние", "полнолуние"]))
                    if phase_elem:
                        phase = phase_elem.get_text(strip=True)[:100]

                    # Знак
                    sign_elem = soup.find(lambda tag: tag.name in ['div', 'p', 'b', 'a'] and ("луна в знаке" in tag.text.lower() or "луна в созвездии" in tag.text.lower()))
                    if sign_elem:
                        sign = sign_elem.get_text(strip=True).replace("Луна в знаке", "").replace("Луна в созвездии", "").strip()[:50]

                    # Текстовое описание
                    text_blocks = soup.find_all('p', class_='article__text')
                    if not text_blocks:
                         text_blocks = soup.find_all('div', class_='article__item__text')
                    
                    # Если все еще пусто, ищем просто абзацы в основном контенте
                    if not text_blocks:
                        content = soup.find('div', {'article-item-type': 'html'})
                        if content:
                            text_blocks = content.find_all('p')

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
