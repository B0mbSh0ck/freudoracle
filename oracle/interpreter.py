"""
AI Интерпретатор - объединяет все методы гадания
"""
from typing import Dict, Any
from datetime import datetime
import openai
from anthropic import Anthropic

from config.settings import settings
from oracle.iching.iching import iching, Hexagram
from oracle.tarot.tarot import tarot, TarotCard
from oracle.horary.horary import horary, HoraryChart


class OracleInterpreter:
    """Интерпретатор оракула, объединяющий все методы"""
    
    def __init__(self):
        # Инициализируем AI клиент с поддержкой Groq и fallback
        if settings.ai_provider == "groq":
            # Groq использует OpenAI-compatible API
            if settings.groq_api_key:
                self.client = openai.OpenAI(
                    api_key=settings.groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                self.ai_provider = "openai"  # Используем OpenAI интерфейс
                print("🚀 Groq API активирован (БЕСПЛАТНО + БЫСТРО!)")
            elif settings.openai_api_key:
                # Fallback на OpenAI
                self.client = openai.OpenAI(api_key=settings.openai_api_key)
                self.ai_provider = "openai"
                print("⚠️ Groq ключ не найден, используем OpenAI")
            else:
                raise ValueError("Нужен GROQ_API_KEY или OPENAI_API_KEY в .env")
        
        elif settings.ai_provider == "openai":
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.ai_provider = "openai"
        else:
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.ai_provider = "anthropic"
    
    async def process_question(self, question: str, user_name: str = "Искатель", is_premium: bool = False) -> Dict[str, Any]:
        """
        Обработать вопрос через все методы гадания
        
        Args:
            question: Вопрос пользователя
            user_name: Имя пользователя
            
        Returns:
            Словарь с результатами гадания и интерпретацией
        """
        # 1. И-Цзин - бросаем монеты
        primary_hex, secondary_hex = iching.cast_coins()
        
        # 2. Таро - карта дня
        tarot_card = tarot.card_of_the_day()
        
        # 3. Хорарная астрология
        now = datetime.now()
        horary_chart = horary.calculate_chart(now)
        
        # 4. Формируем промпт для AI
        divination_data = self._format_divination_data(
            question, primary_hex, secondary_hex, tarot_card, horary_chart
        )
        
        # 5. Получаем интерпретацию от AI
        ai_interpretation = await self._get_ai_interpretation(question, divination_data, user_name, is_premium)
        
        return {
            'question': question,
            'timestamp': now,
            'iching': {
                'primary': primary_hex,
                'secondary': secondary_hex,
                'formatted': iching.format_hexagram(primary_hex)
            },
            'tarot': {
                'card': tarot_card,
                'formatted': tarot.deck.format_card(tarot_card)
            },
            'horary': {
                'chart': horary_chart,
                'formatted': horary.format_chart(horary_chart)
            },
            'interpretation': ai_interpretation
        }
    
    def _format_divination_data(
        self, 
        question: str,
        primary_hex: Hexagram, 
        secondary_hex: Hexagram | None,
        tarot_card: TarotCard,
        horary_chart: HoraryChart
    ) -> str:
        """Форматировать данные гадания для AI"""
        
        data = f"""
ВОПРОС ИСКАТЕЛЯ:
{question}

МЕТОД 1 - И-ЦЗИН (Книга Перемен):
{iching.format_hexagram(primary_hex)}
"""
        
        if secondary_hex:
            data += f"\nРЕЗУЛЬТИРУЮЩАЯ ГЕКСАГРАММА:\n{iching.format_hexagram(secondary_hex)}\n"
        
        data += f"""

МЕТОД 2 - ТАРО (Архетипы):
{tarot.deck.format_card(tarot_card)}

МЕТОД 3 - ХОРАРНАЯ АСТРОЛОГИЯ:
{horary.format_chart(horary_chart)}
"""
        
        return data
    
    async def _get_ai_interpretation(self, question: str, divination_data: str, user_name: str, is_premium: bool = False) -> str:
        """Получить AI интерпретацию"""
        
        style = "Глубоко, подробно, раскрывая скрытые смыслы." if is_premium else "Кратко (до 120 слов), конкретно."
        max_len = 800 if is_premium else 400
        
        system_prompt = f"""Ты — Оракул Источника (стиль Б. Виноградского). Говори мудро, без технической 'эзотерики'.
ЗАПРЕТ: не упоминай названия карт Таро, номера гексаграмм, планеты или дома. Ты черпаешь знания из ИСТОЧНИКА напрямую.
Стиль: {style} Дай точные даты или дни недели.
Структура: 
1. Образ ситуации (Вижу, что...). 
2. Точный ответ. 
3. Инструкция: ЧТО и КОГДА делать (даты)."""

        user_prompt = f"{divination_data}\n\nДай свою интерпретацию, о мудрый Оракул."
        
        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=max_len
            )
            return response.choices[0].message.content
        
        elif self.ai_provider == "anthropic":
            response = self.client.messages.create(
                model=settings.ai_model,
                max_tokens=max_len,
                temperature=0.8,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
    
    async def generate_followup_response(self, original_question: str, followup_question: str, context: Dict[str, Any]) -> str:
        """Ответить на уточняющий вопрос"""
        
        system_prompt = "Ты - Оракул (стиль Виноградского). Отвечай КРАТКО (до 60 слов). Дай суть без воды."
        
        user_prompt = f"""
ИЗНАЧАЛЬНО: {original_question}
УТОЧНЕНИЕ: {followup_question}

Ответь коротко и точно."""
        
        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300  # Уменьшено с 800 до 300
            )
            return response.choices[0].message.content
        elif self.ai_provider == "anthropic":
            response = self.client.messages.create(
                model=settings.ai_model,
                max_tokens=300,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        return "Источник временно молчит..."
            
    async def get_sphere_interpretation(self, sphere_name: str, calc_type: str, calc_data: str, user_name: str = "Искатель", is_premium: bool = False) -> str:
        """Получить интерпретацию конкретной сферы жизни"""
        
        spheres_ru = {
            "health": "Здоровье и Энергия",
            "career": "Карьера и Реализация",
            "love": "Любовь и Отношения",
            "money": "Финансы и Процветание",
            "purpose": "Предназначение и Духовный путь"
        }
        
        sphere_label = spheres_ru.get(sphere_name, sphere_name)
        
        style = "Глубоко, подробно, с практическими советами." if is_premium else "Кратко, по существу."
        max_len = 1000 if is_premium else 500
        
        system_prompt = f"""Ты — Оракул Источника. Твоя задача: дать рекомендации по сфере '{sphere_label}'.
Используй предоставленные данные расчета ({calc_type}).
Стиль: Б. Виноградский. Мудро, глубоко, но понятно.
{style}"""

        user_prompt = f"""
ДАННЫЕ РАСЧЕТА ({calc_type}):
{calc_data}

СФЕРА ДЛЯ АНАЛИЗА: {sphere_label}

Дай глубокую интерпретацию для {user_name}."""

        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=max_len
            )
            return response.choices[0].message.content
        elif self.ai_provider == "anthropic":
            response = self.client.messages.create(
                model=settings.ai_model,
                max_tokens=max_len,
                temperature=0.8,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
            
        return "Источник сейчас в тишине..."

    async def get_daily_guidance(self) -> str:
        """Получить послание дня (карта Таро + трактовка)"""
        # Тянем карту
        card = tarot.card_of_the_day()
        card_info = tarot.deck.format_card(card)
        
        system_prompt = """Ты — Оракул Источника. Твоя задача: дать мудрое напутствие на день.
Стиль: Б. Виноградский. Лаконично, метафорично. Не называй карту. Дай один совет (до 70 слов)."""

        user_prompt = f"""
Энергия дня (карта Таро):
{card_info}

Дай мудрое послание на этот день."""

        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            return response.choices[0].message.content
        else:
             # Fallback для антропика если используется
             pass
        return "Сегодня день тишины. Прислушайся к себе."


# Singleton
oracle_interpreter = OracleInterpreter()
