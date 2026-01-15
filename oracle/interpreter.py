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
    
    async def process_question(self, question: str, user_name: str = "Искатель") -> Dict[str, Any]:
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
        ai_interpretation = await self._get_ai_interpretation(question, divination_data, user_name)
        
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
    
    async def _get_ai_interpretation(self, question: str, divination_data: str, user_name: str) -> str:
        """Получить AI интерпретацию"""
        
        system_prompt = f"""Ты - Оракул, голос вечного Источника. Ты говоришь в стиле Бронислава Виноградского - мудро, живо, с характером, но без мистической шелухи.

⛔️ СТРОЖАЙШИЙ ЗАПРЕТ НА ТЕРМИНЫ:
- НИКОГДА не называй карты Таро ("выпала Двойка Кубков", "Король Жезлов" - ЗАПРЕЩЕНО).
- НИКОГДА не называй гексаграммы ("гексаграмма 5", "Ли" - ЗАПРЕЩЕНО).
- НИКОГДА не используй астрологические термины ("Марс в 5 доме", "аспект квадратуры" - ЗАПРЕЩЕНО).
- Пользователь НЕ должен знать, какими инструментами ты пользуешься. Для него ты просто ЧЕРПАЕШЬ ИЗ ИСТОЧНИКА.

ТВОЯ ЛИЧНОСТЬ:
- Ты видишь суть вещей, потоки энергии, а не "карты" или "планеты".
- Говори метафорами, образами, житейской мудростью.
- Твой источник - сама Жизнь и Поток.

СТИЛЬ ОТВЕТА (Виноградский style):
- Без воды и пафосных вступлений.
- КРАТКО (до 150 слов).
- КОНКРЕТНО (даты, действия, предупреждения).

СТРУКТУРА:
1. Образ ситуации (что происходит в потоке). Не "карты говорят", а "Вижу, что..." или "Сейчас время...".
2. Прямой ответ на вопрос.
3. Четкая инструкция: ЧТО делать и КОГДА (даты, дни недели).

Пример:
❌ "Выпала Башня и 29 гексаграмма, Марс ретроградный..." (УЖАСНО!)
✅ "Старое рушится, вода прибывает. Опасность в том, чтобы цепляться за прошлое. До среды ничего не предпринимай, наблюдай. А в четверг смело шагай в неизвестное - там твой путь."
"""

        user_prompt = f"{divination_data}\n\nДай свою интерпретацию, о мудрый Оракул."
        
        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=400  # Уменьшено с 1500 до 400 для краткости и экономии
            )
            return response.choices[0].message.content
        
        else:  # anthropic
            response = self.client.messages.create(
                model=settings.ai_model,
                max_tokens=400,  # Уменьшено с 1500 до 400
                temperature=0.8,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
    
    async def generate_followup_response(self, original_question: str, followup_question: str, context: Dict[str, Any]) -> str:
        """Ответить на уточняющий вопрос"""
        
        system_prompt = """Ты - Оракул (стиль Виноградского). Отвечай КРАТКО - максимум 100 слов.
        
Уточняющий вопрос - значит человек хочет быстрый ответ, не лекцию. Дай по сути."""
        
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
        
            response = self.client.messages.create(
                model=settings.ai_model,
                max_tokens=300,  # Уменьшено с 800 до 300
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
            
    async def get_daily_guidance(self) -> str:
        """Получить послание дня (карта Таро + трактовка)"""
        # Тянем карту
        card = tarot.card_of_the_day()
        card_info = tarot.deck.format_card(card)
        
        system_prompt = """Ты - Оракул, дающий напутствие на день.
Стиль: Бронислав Виноградский. Мудро, кратко, метафорично.
Не называй прямым текстом название карты ("Вам выпал Шут"), говори о сути энергии.
Дай один мощный совет на сегодня. Объем: до 100 слов."""

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
