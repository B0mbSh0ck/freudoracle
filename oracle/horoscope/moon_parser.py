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
    """Парсер лунного календаря с my-calend.ru"""
    
    BASE_URL = "https://my-calend.ru/moon"

    async def get_moon_info(self, date_str: str = None) -> Optional[MoonInfo]:
        """
        Получить информацию о Луне.
        date_str: 'today', 'tomorrow' или 'yesterday' (или None для сегодня)
        """
        period = date_str if date_str in ['today', 'tomorrow', 'yesterday'] else 'today'
        url = f"{self.BASE_URL}/{period}"
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    lunar_day = "Неизвестно"
                    phase = "Неизвестно"
                    sign = "Неизвестно"
                    description = ""
                    recommendations = ""

                    # 1. Извлекаем основные данные из таблицы .moon-day-info-2
                    info_table = soup.select_one('table.moon-day-info-2')
                    if info_table:
                        for row in info_table.find_all('tr'):
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                label = cells[0].get_text(strip=True).lower()
                                value = cells[1].get_text(strip=True)
                                
                                if "лунные сутки" in label:
                                    lunar_day = value
                                elif "фаза луны" in label:
                                    phase = value
                                elif "луна в знаке" in label:
                                    sign = value

                    # 2. Общее описание (первый абзац в .moon-day или после таблицы)
                    # Обычно это краткое резюме дня
                    main_container = soup.select_one('div.moon-day')
                    if main_container:
                        summary_p = main_container.find('p')
                        if summary_p:
                            description = summary_p.get_text(strip=True)

                    # 3. Детальные рекомендации (из блока влияния)
                    influence_section = soup.select_one('section.moon-today-influence')
                    if influence_section:
                        articles = influence_section.find_all('article')
                        recs_list = []
                        for article in articles:
                            h3 = article.find('h3')
                            p = article.find('p')
                            if h3 and p:
                                title = h3.get_text(strip=True)
                                text = p.get_text(strip=True)
                                # Берем первые 2-3 предложения или ограничиваем длину
                                if len(text) > 200:
                                    text = text[:197] + "..."
                                recs_list.append(f"🔹 *{title}:*\n{text}")
                        
                        if recs_list:
                            recommendations = "\n\n".join(recs_list[:3]) # Берем первые 3 важных блока

                    # Если рекомендаций нет в блоке влияния, пробуем найти другие абзацы
                    if not recommendations and main_container:
                        all_ps = main_container.find_all('p')
                        if len(all_ps) > 1:
                            recommendations = all_ps[1].get_text(strip=True)

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
🌙 *ЛУННЫЙ КАЛЕНДАРЬ*

🗓 *{moon.lunar_day}*
🌕 Фаза: *{moon.phase}*
♈ Луна в знаке: *{moon.sign}*

📖 *Общее влияние:*
_{moon.description}_

💡 *Детальный прогноз:*
{moon.recommendations}

_Источник: my-calend.ru_
"""

moon_parser = MoonParser()
