"""
Матрица Судьбы (Matrix of Destiny)
Расчет по дате рождения на основе 22 Арканов Таро
"""
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class DestinyMatrix:
    """Матрица судьбы"""
    birth_date: datetime
    
    # Основные энергии (Арканы 1-22)
    personal_arcana: int  # Личный Аркан
    destiny_arcana: int  # Аркан Судьбы
    social_arcana: int  # Социальный Аркан
    spiritual_arcana: int  # Духовный Аркан
    
    # Чакровая линия (7 чакр)
    chakra_line: List[int]
    
    # Линия здоровья
    health_arcana: int
    
    # Денежный канал
    money_arcana: int
    
    # Программы (кармические задачи)
    parent_program: int  # От родителей
    love_program: int  # Отношения
    talent_program: int  # Таланты
    
    # Годовые энергии
    current_year_arcana: int
    
    # Интерпретации
    arcana_meanings: Dict[str, str]
    challenges: List[str]
    talents: List[str]
    purpose: str


class MatrixOfDestiny:
    """Расчет Матрицы Судьбы"""
    
    # Значения 22 Арканов
    ARCANA_MEANINGS = {
        0: {
            'name': 'Шут',
            'energy': 'Свобода, спонтанность, новые начинания',
            'challenge': 'Безрассудность, инфантильность',
            'talent': 'Способность начинать с чистого листа'
        },
        1: {
            'name': 'Маг',
            'energy': 'Действие, мастерство, проявление',
            'challenge': 'Манипуляции, иллюзии',
            'talent': 'Способность материализовывать идеи'
        },
        2: {
            'name': 'Верховная Жрица',
            'energy': 'Интуиция, тайна, подсознание',
            'challenge': 'Секреты, замкнутость',
            'talent': 'Глубокая интуиция и ясновидение'
        },
        3: {
            'name': 'Императрица',
            'energy': 'Изобилие, материнство, творчество',
            'challenge': 'Чрезмерная опека, зависимость',
            'talent': 'Способность творить и взращивать'
        },
        4: {
            'name': 'Император',
            'energy': 'Власть, структура, контроль',
            'challenge': 'Тирания, жесткость',
            'talent': 'Лидерство и организация'
        },
        5: {
            'name': 'Иерофант',
            'energy': 'Традиции, учение, духовность',
            'challenge': 'Догматизм, консерватизм',
            'talent': 'Передача знаний и мудрости'
        },
        6: {
            'name': 'Влюбленные',
            'energy': 'Выбор, любовь, союз',
            'challenge': 'Нерешительность, зависимые отношения',
            'talent': 'Гармония в отношениях'
        },
        7: {
            'name': 'Колесница',
            'energy': 'Победа, контроль, движение вперед',
            'challenge': 'Агрессия, потеря контроля',
            'talent': 'Целеустремленность и воля'
        },
        8: {
            'name': 'Сила',
            'energy': 'Внутренняя сила, терпение, сострадание',
            'challenge': 'Слабость, неуверенность',
            'talent': 'Управление энергией через любовь'
        },
        9: {
            'name': 'Отшельник',
            'energy': 'Мудрость, поиск истины, одиночество',
            'challenge': 'Изоляция, отчуждение',
            'talent': 'Глубокое понимание и наставничество'
        },
        10: {
            'name': 'Колесо Фортуны',
            'energy': 'Судьба, циклы, перемены',
            'challenge': 'Зависимость от удачи, нестабильность',
            'talent': 'Способность использовать возможности'
        },
        11: {
            'name': 'Справедливость',
            'energy': 'Баланс, истина, закон',
            'challenge': 'Жесткость, бескомпромиссность',
            'talent': 'Объективность и честность'
        },
        12: {
            'name': 'Повешенный',
            'energy': 'Жертва, новая перспектива, пауза',
            'challenge': 'Застой, мученичество',
            'talent': 'Способность видеть с другой стороны'
        },
        13: {
            'name': 'Смерть',
            'energy': 'Трансформация, окончание, обновление',
            'challenge': 'Страх перемен, застревание в прошлом',
            'talent': 'Мощная трансформирующая сила'
        },
        14: {
            'name': 'Умеренность',
            'energy': 'Гармония, баланс, исцеление',
            'challenge': 'Излишества, дисбаланс',
            'talent': 'Алхимия и целительство'
        },
        15: {
            'name': 'Дьявол',
            'energy': 'Материальность, страсть, привязанность',
            'challenge': 'Зависимости, одержимость',
            'talent': 'Мощная сексуальная и материальная энергия'
        },
        16: {
            'name': 'Башня',
            'energy': 'Разрушение иллюзий, откровение, шок',
            'challenge': 'Катастрофы, внезапные потери',
            'talent': 'Способность к прорыву и обновлению'
        },
        17: {
            'name': 'Звезда',
            'energy': 'Надежда, вдохновение, исцеление',
            'challenge': 'Разочарование, нереалистичность',
            'talent': 'Вдохновение и целительная энергия'
        },
        18: {
            'name': 'Луна',
            'energy': 'Подсознание, иллюзии, интуиция',
            'challenge': 'Страхи, обманы, неясность',
            'talent': 'Глубокая интуиция и связь с подсознанием'
        },
        19: {
            'name': 'Солнце',
            'energy': 'Радость, успех, витальность',
            'challenge': 'Эгоизм, высокомерие',
            'talent': 'Сияние и способность вдохновлять'
        },
        20: {
            'name': 'Суд',
            'energy': 'Возрождение, призвание, прощение',
            'challenge': 'Осуждение, вина',
            'talent': 'Пробуждение и трансформация'
        },
        21: {
            'name': 'Мир',
            'energy': 'Завершение, целостность, успех',
            'challenge': 'Незавершенность, застревание',
            'talent': 'Достижение мастерства и целостности'
        },
        22: {
            'name': 'Шут (22)',
            'energy': 'Высшая свобода, просветление',
            'challenge': 'Безумие, хаос',
            'talent': 'Трансцендентность'
        }
    }
    
    def calculate_matrix(self, birth_date: datetime) -> DestinyMatrix:
        """Рассчитать Матрицу Судьбы"""
        
        day = birth_date.day
        month = birth_date.month
        year = birth_date.year
        
        # 1. Личный Аркан (день рождения)
        personal_arcana = self._reduce_to_arcana(day)
        
        # 2. Аркан Судьбы (месяц)
        destiny_arcana = self._reduce_to_arcana(month)
        
        # 3. Социальный Аркан (год)
        social_arcana = self._reduce_to_arcana(year)
        
        # 4. Духовный Аркан (сумма всех)
        spiritual_arcana = self._reduce_to_arcana(
            personal_arcana + destiny_arcana + social_arcana
        )
        
        # 5. Чакровая линия (7 чакр)
        chakra_line = self._calculate_chakra_line(birth_date)
        
        # 6. Здоровье
        health_arcana = self._reduce_to_arcana(day + month)
        
        # 7. Деньги
        money_arcana = self._reduce_to_arcana(day + year)
        
        # 8. Программы
        parent_program = self._reduce_to_arcana(day + month + year)
        love_program = self._reduce_to_arcana(personal_arcana + destiny_arcana)
        talent_program = self._reduce_to_arcana(personal_arcana + social_arcana)
        
        # 9. Текущий год
        current_year = datetime.now().year
        current_year_arcana = self._reduce_to_arcana(
            day + month + current_year
        )
        
        # Формируем интерпретации
        arcana_meanings = {
            'personal': f"{self.ARCANA_MEANINGS[personal_arcana]['name']}: {self.ARCANA_MEANINGS[personal_arcana]['energy']}",
            'destiny': f"{self.ARCANA_MEANINGS[destiny_arcana]['name']}: {self.ARCANA_MEANINGS[destiny_arcana]['energy']}",
            'social': f"{self.ARCANA_MEANINGS[social_arcana]['name']}: {self.ARCANA_MEANINGS[social_arcana]['energy']}",
            'spiritual': f"{self.ARCANA_MEANINGS[spiritual_arcana]['name']}: {self.ARCANA_MEANINGS[spiritual_arcana]['energy']}"
        }
        
        # Вызовы
        challenges = [
            self.ARCANA_MEANINGS[personal_arcana]['challenge'],
            self.ARCANA_MEANINGS[destiny_arcana]['challenge'],
            self.ARCANA_MEANINGS[parent_program]['challenge']
        ]
        
        # Таланты
        talents = [
            self.ARCANA_MEANINGS[personal_arcana]['talent'],
            self.ARCANA_MEANINGS[talent_program]['talent']
        ]
        
        # Предназначение
        purpose = f"Ваше предназначение связано с энергией Аркана {spiritual_arcana} - {self.ARCANA_MEANINGS[spiritual_arcana]['name']}"
        
        return DestinyMatrix(
            birth_date=birth_date,
            personal_arcana=personal_arcana,
            destiny_arcana=destiny_arcana,
            social_arcana=social_arcana,
            spiritual_arcana=spiritual_arcana,
            chakra_line=chakra_line,
            health_arcana=health_arcana,
            money_arcana=money_arcana,
            parent_program=parent_program,
            love_program=love_program,
            talent_program=talent_program,
            current_year_arcana=current_year_arcana,
            arcana_meanings=arcana_meanings,
            challenges=challenges,
            talents=talents,
            purpose=purpose
        )
    
    def _reduce_to_arcana(self, number: int) -> int:
        """Свести число к Аркану (0-22)"""
        while number > 22:
            number = sum(int(digit) for digit in str(number))
        return number
    
    def _calculate_chakra_line(self, birth_date: datetime) -> List[int]:
        """Рассчитать линию чакр"""
        day = birth_date.day
        month = birth_date.month
        year = birth_date.year
        
        # 7 чакр
        chakras = []
        chakras.append(self._reduce_to_arcana(day))  # Муладхара (корневая)
        chakras.append(self._reduce_to_arcana(month))  # Свадхистана (сакральная)
        chakras.append(self._reduce_to_arcana(year))  # Манипура (солнечное сплетение)
        chakras.append(self._reduce_to_arcana(day + month))  # Анахата (сердечная)
        chakras.append(self._reduce_to_arcana(month + year))  # Вишудха (горловая)
        chakras.append(self._reduce_to_arcana(day + year))  # Аджна (третий глаз)
        chakras.append(self._reduce_to_arcana(day + month + year))  # Сахасрара (коронная)
        
        return chakras
    
    def format_matrix(self, matrix: DestinyMatrix) -> str:
        """Форматировать Матрицу Судьбы для отображения"""
        result = f"""
🔮 **МАТРИЦА СУДЬБЫ**

**Дата рождения:** {matrix.birth_date.strftime('%d.%m.%Y')}

**🌟 ОСНОВНЫЕ ЭНЕРГИИ:**
• Личный Аркан: **{matrix.personal_arcana}** - {matrix.arcana_meanings['personal']}
• Аркан Судьбы: **{matrix.destiny_arcana}** - {matrix.arcana_meanings['destiny']}
• Социальный Аркан: **{matrix.social_arcana}** - {matrix.arcana_meanings['social']}
• Духовный Аркан: **{matrix.spiritual_arcana}** - {matrix.arcana_meanings['spiritual']}

**🧘 ЧАКРОВАЯ ЛИНИЯ:**
1. Муладхара: {matrix.chakra_line[0]}
2. Свадхистана: {matrix.chakra_line[1]}
3. Манипура: {matrix.chakra_line[2]}
4. Анахата: {matrix.chakra_line[3]}
5. Вишудха: {matrix.chakra_line[4]}
6. Аджна: {matrix.chakra_line[5]}
7. Сахасрара: {matrix.chakra_line[6]}

**💰 КАНАЛЫ:**
• Здоровье: Аркан {matrix.health_arcana}
• Деньги: Аркан {matrix.money_arcana}

**📋 ПРОГРАММЫ:**
• Родительская: Аркан {matrix.parent_program}
• Любовь: Аркан {matrix.love_program}
• Таланты: Аркан {matrix.talent_program}

**⏰ ЭНЕРГИЯ ТЕКУЩЕГО ГОДА:**
Аркан **{matrix.current_year_arcana}** - {self.ARCANA_MEANINGS[matrix.current_year_arcana]['name']}

**🎯 ПРЕДНАЗНАЧЕНИЕ:**
{matrix.purpose}

**✨ ВАШИ ТАЛАНТЫ:**
{chr(10).join(f"• {talent}" for talent in matrix.talents)}

**⚠️ ВЫЗОВЫ ДЛЯ ПРОРАБОТКИ:**
{chr(10).join(f"• {challenge}" for challenge in matrix.challenges)}
"""
        return result.strip()


# Singleton
matrix_of_destiny = MatrixOfDestiny()
