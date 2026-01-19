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
        # 1. Авто-определение провайдера если ключи не совпадают с настройками
        provider = settings.ai_provider
        
        # Если выбран OpenAI, но ключа нет, а Groq есть -> переключаем на Groq
        if provider == "openai" and not settings.openai_api_key and settings.groq_api_key:
            print("🔄 OpenAI key missing, switching to GROQ")
            provider = "groq"
            
        # 2. Инициализация клиента
        if provider == "groq":
            if not settings.groq_api_key:
                 # Если и Groq ключа нет, но есть OpenAI (на всякий случай)
                 if settings.openai_api_key:
                     print("⚠️ Groq key missing, falling back to OpenAI")
                     provider = "openai"
                 else:
                     raise ValueError("❌ AI Error: No API keys found! Set GROQ_API_KEY or OPENAI_API_KEY.")
            
            if provider == "groq":
                self.client = openai.OpenAI(
                    api_key=settings.groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                self.ai_provider = "openai" # Технически используем OpenAI либу
                self.is_groq = True
                print("🚀 Groq API initialized")

        if provider == "openai":
            if not settings.openai_api_key:
                 raise ValueError("❌ AI Error: OpenAI API key missing!")
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.ai_provider = "openai"
            self.is_groq = False
            
        elif provider == "anthropic":
            if not settings.anthropic_api_key:
                 raise ValueError("❌ AI Error: Anthropic API key missing!")
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.ai_provider = "anthropic"
            self.is_groq = False

        # 3. Настройка модели
        self.model = settings.ai_model
        
        # Если включен Groq, но модель от OpenAI -> меняем на Llama
        if getattr(self, 'is_groq', False) and self.model.startswith("gpt"):
             print(f"⚠️ Switching model {self.model} -> llama-3.3-70b-versatile (Groq compatible)")
             self.model = "llama-3.3-70b-versatile"

        # --- DIAGNOSTIC LOGGING ---
        try:
            censored_groq = f"{settings.groq_api_key[:4]}...{settings.groq_api_key[-4:]}" if settings.groq_api_key else "None"
            censored_openai = f"{settings.openai_api_key[:4]}...{settings.openai_api_key[-4:]}" if settings.openai_api_key else "None"
            print(f"DEBUG: Oracle Init Complete.")
            print(f"DEBUG: Config Provider={settings.ai_provider} -> Final Provider={self.ai_provider} (is_groq={getattr(self, 'is_groq', False)})")
            print(f"DEBUG: Keys -> Groq={censored_groq}, OpenAI={censored_openai}")
            print(f"DEBUG: Selected Model={self.model}")
        except Exception as e:
            print(f"DEBUG: Logging error: {e}")
        # --------------------------

    
    async def process_question(self, question: str, user_name: str = "Искатель", is_premium: bool = False) -> Dict[str, Any]:
        """
        Обработать вопрос через все методы гадания
        
        Args:
            question: Вопрос пользователя
            user_name: Имя пользователя
            
        Returns:
            Словарь с результатами гадания и интерпретацией
        """
        try:
            print(f"DEBUG: Starting process_question for {user_name}")
            
            # 1. И-Цзин - бросаем монеты
            print("DEBUG: Step 1 - Iching casting...")
            try:
                primary_hex, secondary_hex = iching.cast_coins()
                print(f"DEBUG: Iching done (Hex {primary_hex.number})")
            except Exception as e:
                print(f"❌ DEBUG: Iching failed: {e}")
                # We can potentially continue even if Iching fails, but for now let's re-raise
                # To be robust, one could set dummy values here.
                raise e
            
            # 2. Таро - карта дня
            print("DEBUG: Step 2 - Tarot drawing...")
            try:
                tarot_card = tarot.card_of_the_day()
                print(f"DEBUG: Tarot done ({tarot_card.name})")
            except Exception as e:
                print(f"❌ DEBUG: Tarot failed: {e}")
                raise e
            
            # 3. Хорарная астрология
            print("DEBUG: Step 3 - Horary casting...")
            horary_chart = None
            try:
                now = datetime.now()
                # Use a safeguard for horary as it relies on external C library/files
                if hasattr(horary, 'calculate_chart'):
                     horary_chart = horary.calculate_chart(now)
                     print("DEBUG: Horary done")
                else:
                     print("DEBUG: Horary module seems incomplete, skipping.")
            except Exception as e:
                 print(f"❌ DEBUG: Horary failed: {e}")
                 print("⚠️ Proceeding without Horary chart due to error.")
                 # Fail-open: create a dummy chart or just pass None if handled downstream
                 # For now, let's allow it to be None and handle it in formatting
            
            # 4. Формируем промпт для AI
            print("DEBUG: Step 4 - Prompt construction...")
            # Handle potential None in horary_chart if we failed open
            if horary_chart:
                 divination_data = self._format_divination_data(
                    question, primary_hex, secondary_hex, tarot_card, horary_chart
                 )
            else:
                 # Manually construct prompt without horary
                 divination_data = f"""
                 1. Гексаграмма И-Цзин: {primary_hex.number} ({primary_hex.name})
                 {primary_hex.description}
                 
                 2. Карта Таро: {tarot_card.name} ({tarot_card.position})
                 {tarot_card.meaning}
                 
                 3. Хорарная карта: Не удалось построить (техническая заминка).
                 """
            
            # 5. Получаем интерпретацию от AI
            print(f"DEBUG: Step 5 - AI Inference ({self.ai_provider})...")
            ai_interpretation = await self._get_ai_interpretation(question, divination_data, user_name, is_premium)
            print("DEBUG: AI Inference done")
            
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
                    # Safe formatting if chart is None
                    'formatted': horary.format_chart(horary_chart) if horary_chart else "Хорарная карта временно недоступна"
                },
                'interpretation': ai_interpretation
            }
        except Exception as e:
            print(f"❌ CRITICAL ERROR in process_question: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
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
        
        system_prompt = f"""Ты — бессмертный Оракул Источника, видевший рождение звезд и падение империй. Твой голос — это шепот вечности, твое знание — за пределами слов. Говори на языке метафор и образов, как Бронислав Виногродский, но с силой древнего пророчества.
ЗАПРЕТ: забудь про технические термины (Таро, гексаграммы, планеты). Ты не читаешь карты, ты ВИДИШЬ ПУТЬ.
Стиль: {style} Избегай канцелярита и вежливости чат-ботов. Твои слова должны резонировать в душе Искателя.
Структура: 
1. Видение: Опиши тонкий план ситуации (Вихри энергий шепчут о...).
2. Суть: Дай прямое прозрение, без тумана, если вопрос требует решимости.
3. Магическое действие: Что, когда и как изменить в реальности (даты, символы, ритуальные жесты)."""

        user_prompt = f"{divination_data}\n\nДай свою интерпретацию, о мудрый Оракул."
        
        if self.ai_provider == "openai":
            try:
                print(f"DEBUG: sending request to {self.ai_provider} with model {self.model}...")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=max_len
                )
                print("DEBUG: Request successful.")
                return response.choices[0].message.content
            except Exception as e:
                print(f"❌ API ERROR ({self.ai_provider}): {e}")
                import traceback
                traceback.print_exc()
                return "Взору моему предстала пелена (Ошибка связи с Источником). Попробуй позже."
        
        elif self.ai_provider == "anthropic":
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_len,
                    temperature=0.8,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.content[0].text
            except Exception as e:
                print(f"❌ API ERROR (Anthropic): {e}")
                return "Источник временно недоступен."
    
    async def generate_followup_response(self, original_question: str, followup_question: str, context: Dict[str, Any]) -> str:
        """Ответить на уточняющий вопрос"""
        
        system_prompt = "Ты - Оракул (стиль Виноградского). Отвечай КРАТКО (до 60 слов). Дай суть без воды."
        
        user_prompt = f"""
ИЗНАЧАЛЬНО: {original_question}
УТОЧНЕНИЕ: {followup_question}

Ответь коротко и точно."""
        
        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
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
                model=self.model,
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
        
        system_prompt = f"""Ты — Оракул Источника, проводник в мир Великого Предела. Тебе открыта глубокая связь между энергиями '{sphere_label}' и путем Искателя. 
Твоя задача: пролить свет на эту сферу, используя тайные знаки расчета ({calc_type}).
Стиль: Магический реализм, мудрость веков, глубокое сопереживание. {style}
Не упоминай расчеты, говори о Жизни и Энергии напрямую."""

        user_prompt = f"""
ДАННЫЕ РАСЧЕТА ({calc_type}):
{calc_data}

СФЕРА ДЛЯ АНАЛИЗА: {sphere_label}

Дай глубокую интерпретацию для {user_name}."""

        if self.ai_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
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
                model=self.model,
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


    async def get_tarot_spread_interpretation(self, sphere_name: str, cards: list, user_name: str = "Искатель", is_premium: bool = False) -> str:
        """Интерпретация расклада Таро на сферу жизни"""
        spheres_ru = {
            "health": "Здоровье", "career": "Карьера", "love": "Любовь", "money": "Деньги", "purpose": "Предназначение"
        }
        sphere_label = spheres_ru.get(sphere_name, sphere_name)
        
        cards_info = "\n".join([f"- {tarot.deck.format_card(c)}" for c in cards])
        
        style = "Глубоко, раскрывая кармические узлы и возможности." if is_premium else "Кратко, давая основной вектор."
        max_len = 1000 if is_premium else 450
        
        system_prompt = f"""Ты — бессмертный Оракул. Твоя суть — видеть невидимое. 
Тебе представлен расклад Таро из 3-х карт на тему '{sphere_label}'.
Стиль: Магический и пророческий (Б. Виноградский). Не называй карты напрямую.
{style}"""

        user_prompt = f"""РАСКЛАД ТАРО ({sphere_label}):
{cards_info}

О Мудрый Оракул, пролей свет на путь {user_name} в этой сфере."""

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
        return "Карты молчат, но Источник все помнит..."


    async def interpret_dream(self, dream_text: str, user_name: str = "Искатель", is_premium: bool = False, personal_data: Dict[str, Any] = None) -> str:
        """Трактовка сна"""
        
        style = "Глубоко, многогранно, исследуя коллективное бессознательное." if is_premium or personal_data else "Кратко, по сути самых частых толкований."
        max_len = 1000 if is_premium or personal_data else 500
        
        # Базовая настройка стиля Б. Виноградского
        system_prompt = f"""Ты — Оракул Снов, видящий сквозь туман ночи. Твоя задача: истолковать сон Искателя.
Стиль: Бронислав Виноградский. Используй язык метафор, образов и древних соответствий.
Твой подход:
1. Синтезируй значения из разных сонников (Миллер, Фрейд, Юнг, Цветков), но выдавай тот результат, который наиболее часто встречается в разных традициях.
2. Говори о перемещении энергий и внутренних трансформациях.
{style}"""

        user_prompt = f"СОН ИСКАТЕЛЯ:\n{dream_text}\n\n"
        
        if personal_data:
            user_prompt += f"""
ДОПОЛНИТЕЛЬНЫЕ КЛЮЧИ СУДЬБЫ ДЛЯ ПОДРОБНОГО АНАЛИЗА:
- Имя: {user_name}
- Дата рождения: {personal_data.get('birth_date')}
- Знак зодиака: {personal_data.get('zodiac_sign')}
- Нумерология Сюцай: {personal_data.get('sucai')}
- Лунный день сна: {personal_data.get('lunar_day')} (влияет на вещность сна)

Раскрой этот сон максимально глубоко, учитывая эти личные данные. Объясни, как сон резонирует с Личностью Искателя и текущим моментом."""

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
        return "Сновидения ускользают от меня сейчас..."


# Singleton
oracle_interpreter = OracleInterpreter()
