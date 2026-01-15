"""
Генератор психологических ритуалов
Основано на методе Бронислава Виногродского
"""
from typing import Dict, Any
import openai
from anthropic import Anthropic

from config.settings import settings


class RitualGenerator:
    """Генератор психологических ритуалов для решения проблем"""
    
    def __init__(self):
        if settings.ai_provider == "openai":
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.ai_provider = "openai"
        else:
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.ai_provider = "anthropic"
    
    async def generate_ritual(self, question: str, oracle_response: Dict[str, Any]) -> str:
        """
        Сгенерировать психологический ритуал
        
        Args:
            question: Изначальный вопрос
            oracle_response: Ответ оракула с гаданием
            
        Returns:
            Описание ритуала
        """
        
        system_prompt = """Ты - мастер даосских и психологических практик, последователь Бронислава Виногродского.

Твоя задача - создать персональный психологический РИТУАЛ для человека, который поможет ему трансформировать ситуацию.

ПРИНЦИПЫ РИТУАЛА (по Виногродскому):
1. Ритуал - это ДЕЙСТВИЕ, а не просто размышление
2. Он должен быть конкретным и выполнимым
3. Включает элементы:
   - Подготовка пространства
   - Работа с телом (движение, дыхание)
   - Работа с предметами (символизм)
   - Вербальная формула или аффирмация
   - Завершение и интеграция
4. Основано на принципах И-Цзин и даосизма
5. Использует метафоры стихий (вода, огонь, дерево, металл, земля)

СТРУКТУРА РИТУАЛА:
1. *Название ритуала* (короткое, символичное)
2. *Цель* (что трансформируется)
3. *Необходимые элементы* (простые предметы)
4. *Время и место* (когда и где выполнять)
5. *Пошаговое описание* (конкретные действия)
6. *Завершение* (как интегрировать опыт)

СТИЛЬ:
- Поэтичный, но конкретный
- Используй символизм И-Цзин и Таро
- Длина: 400-600 слов
- Ритуал должен занимать 15-30 минут выполнения"""

        # Извлекаем данные из ответа оракула
        iching_info = oracle_response.get('iching', {}).get('formatted', '')
        tarot_info = oracle_response.get('tarot', {}).get('formatted', '')
        interpretation = oracle_response.get('interpretation', '')
        
        user_prompt = f"""
ВОПРОС ЧЕЛОВЕКА:
{question}

ПОСЛАНИЕ ОРАКУЛА:
{interpretation}

И-ЦЗИН:
{iching_info}

ТАРО:
{tarot_info}

Создай персональный психологический ритуал для этого человека, который поможет ему трансформировать ситуацию.
Используй символизм из гадания (гексаграммы, карты, стихии)."""
        
        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.85,
                max_tokens=2000
            )
            return response.choices[0].message.content
        
        else:  # anthropic
            response = self.client.messages.create(
                model=settings.ai_model,
                max_tokens=2000,
                temperature=0.85,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text


# Singleton
ritual_generator = RitualGenerator()
