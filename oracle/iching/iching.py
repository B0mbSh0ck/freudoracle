"""
Модуль И-Цзин (Книга Перемен)
Генерация гексаграмм методом бросания монет
"""
import random
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Hexagram:
    """Гексаграмма И-Цзин"""
    number: int
    name_chinese: str
    name_russian: str
    name_pinyin: str
    trigram_above: str
    trigram_below: str
    lines: List[int]  # 6 линий: 6 (старая инь), 7 (молодая ян), 8 (молодая инь), 9 (старая ян)
    changing_lines: List[int]  # индексы изменяющихся линий
    interpretation: str
    judgment: str
    image: str


class IChing:
    """Класс для работы с И-Цзин"""
    
    def __init__(self):
        self.hexagrams = self._load_hexagrams()
    
    def cast_coins(self) -> Tuple[Hexagram, Hexagram | None]:
        """
        Бросание трех монет 6 раз для получения гексаграммы
        
        Returns:
            Tuple[Hexagram, Hexagram | None]: 
                - Исходная гексаграмма
                - Результирующая гексаграмма (если есть изменяющиеся линии)
        """
        lines = []
        changing_lines = []
        
        for i in range(6):
            # Бросаем 3 монеты (орел=3, решка=2)
            coins = [random.choice([2, 3]) for _ in range(3)]
            line_value = sum(coins)
            lines.append(line_value)
            
            # Старые линии (6 и 9) - изменяющиеся
            if line_value in [6, 9]:
                changing_lines.append(i)
        
        # Находим гексаграмму по линиям
        primary_hex = self._get_hexagram_by_lines(lines)
        
        # Если есть изменяющиеся линии, создаем результирующую гексаграмму
        secondary_hex = None
        if changing_lines:
            transformed_lines = lines.copy()
            for idx in changing_lines:
                # 6 (старая инь) -> 7 (молодая ян)
                # 9 (старая ян) -> 8 (молодая инь)
                if transformed_lines[idx] == 6:
                    transformed_lines[idx] = 7
                elif transformed_lines[idx] == 9:
                    transformed_lines[idx] = 8
            
            secondary_hex = self._get_hexagram_by_lines(transformed_lines)
        
        return primary_hex, secondary_hex
    
    def _get_hexagram_by_lines(self, lines: List[int]) -> Hexagram:
        """Получить гексаграмму по значениям линий"""
        # Преобразуем линии в бинарный код
        # 6, 8 = инь (0), 7, 9 = ян (1)
        binary = []
        for line in lines:
            if line in [6, 8]:  # инь
                binary.append(0)
            else:  # ян (7, 9)
                binary.append(1)
        
        # Находим номер гексаграммы
        hex_number = self._binary_to_hexagram_number(binary)
        
        # Получаем гексаграмму из базы данных
        hexagram_data = self.hexagrams.get(hex_number, self.hexagrams[1])
        
        changing_lines = [i for i, line in enumerate(lines) if line in [6, 9]]
        
        return Hexagram(
            number=hex_number,
            name_chinese=hexagram_data['name_chinese'],
            name_russian=hexagram_data['name_russian'],
            name_pinyin=hexagram_data['name_pinyin'],
            trigram_above=hexagram_data['trigram_above'],
            trigram_below=hexagram_data['trigram_below'],
            lines=lines,
            changing_lines=changing_lines,
            interpretation=hexagram_data['interpretation'],
            judgment=hexagram_data['judgment'],
            image=hexagram_data['image']
        )
    
    def _binary_to_hexagram_number(self, binary: List[int]) -> int:
        """
        Преобразовать бинарный код линий в номер гексаграммы (1-64)
        binary: список из 6 элементов [нижняя ... верхняя]
        """
        # Используем стандартную схему нумерации И-Цзин
        # Для простоты используем формулу (может отличаться от классической нумерации)
        number = 0
        for i, bit in enumerate(binary):
            number += bit * (2 ** i)
        
        # Мапим на диапазон 1-64
        return (number % 64) + 1
    
    def _load_hexagrams(self) -> dict:
        """Загрузить базу данных гексаграмм"""
        import json
        import os
        
        # Пытаемся загрузить из JSON файла
        json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'iching_hexagrams.json')
        
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Преобразуем список в словарь с ключами-номерами
                    return {hex_data['number']: hex_data for hex_data in data['hexagrams']}
        except Exception as e:
            print(f"Warning: Could not load hexagrams from JSON: {e}")
        
        # Fallback - встроенные данные (первые 3 гексаграммы)
        return {
            1: {
                'name_chinese': '乾',
                'name_russian': 'Творчество',
                'name_pinyin': 'Qián',
                'trigram_above': '☰ Небо',
                'trigram_below': '☰ Небо',
                'interpretation': 'Время активных действий. Сильная творческая энергия. Все начинания благоприятны.',
                'judgment': 'Изначальное свершение. Благоприятна стойкость.',
                'image': 'Движение неба полно силы. Благородный человек делает себя сильным и неутомимым.'
            },
            2: {
                'name_chinese': '坤',
                'name_russian': 'Исполнение',
                'name_pinyin': 'Kūn',
                'trigram_above': '☷ Земля',
                'trigram_below': '☷ Земля',
                'interpretation': 'Время восприимчивости и преданности. Следуй за ведущим. Покорность приносит успех.',
                'judgment': 'Изначальное свершение. Благоприятна стойкость кобылицы.',
                'image': 'Состояние земли - исполнение. Благородный человек широкой добродетелью несет все вещи.'
            },
            3: {
                'name_chinese': '屯',
                'name_russian': 'Начальная трудность',
                'name_pinyin': 'Zhūn',
                'trigram_above': '☵ Вода',
                'trigram_below': '☳ Гром',
                'interpretation': 'Период трудностей в начале. Нужна настойчивость. Не спеши, организуй помощников.',
                'judgment': 'Изначальное свершение. Благоприятна стойкость. Не следует что-либо предпринимать.',
                'image': 'Облака и гром. Благородный человек упорядочивает и систематизирует.'
            }
        }
    
    def get_line_symbol(self, line_value: int) -> str:
        """Получить символ линии"""
        symbols = {
            6: '⚋ ← (старая инь, изменяется)',
            7: '⚊ (молодая ян)',
            8: '⚋ (молодая инь)',
            9: '⚊ ← (старая ян, изменяется)'
        }
        return symbols.get(line_value, '?')
    
    def format_hexagram(self, hexagram: Hexagram) -> str:
        """Форматировать гексаграмму для отображения"""
        lines_str = "\n".join([
            f"{6-i}. {self.get_line_symbol(line)}" 
            for i, line in enumerate(reversed(hexagram.lines))
        ])
        
        result = f"""
🔮 *Гексаграмма #{hexagram.number}*
{hexagram.name_chinese} ({hexagram.name_pinyin})
*{hexagram.name_russian}*

*Триграммы:*
Верхняя: {hexagram.trigram_above}
Нижняя: {hexagram.trigram_below}

*Линии:*
{lines_str}

*Суждение:*
{hexagram.judgment}

*Образ:*
{hexagram.image}

*Интерпретация:*
{hexagram.interpretation}
"""
        
        if hexagram.changing_lines:
            result += f"\n*Изменяющиеся линии:* {', '.join(str(i+1) for i in hexagram.changing_lines)}"
        
        return result.strip()


# Singleton instance
iching = IChing()
