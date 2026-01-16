
from datetime import datetime
import random

class CompatibilityCalculator:
    """Калькулятор совместимости (Сюцай + Матрица + Биоритмы)"""

    def calculate(self, date1: datetime, date2: datetime) -> dict:
        """
        Рассчитать совместимость двух дат
        """
        score_sucai = self._calc_sucai_compatibility(date1, date2)
        score_matrix = self._calc_matrix_compatibility(date1, date2)
        score_biorhythm = self._calc_biorhythm(date1, date2)
        
        # Среднее взвешенное
        total_score = int((score_sucai * 0.3) + (score_matrix * 0.3) + (score_biorhythm * 0.4))
        
        return {
            "total_score": total_score,
            "details": {
                "sucai": score_sucai,
                "matrix": score_matrix,
                "biorhythm": score_biorhythm
            },
            "text_report": self._generate_report(total_score)
        }
    
    def render_speedometer(self, percent: int) -> str:
        """Отрисовать спидометр прогресс-баром"""
        bar_length = 10
        filled_length = int(bar_length * percent / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Цвет (эмодзи) в зависимости от %
        if percent < 40: emoji = "🔴"
        elif percent < 70: emoji = "🟡"
        else: emoji = "🟢"
        
        return f"{emoji} [{bar}] {percent}%"

    def _calc_sucai_compatibility(self, d1: datetime, d2: datetime) -> int:
        """Упрощенная совместимость по числу сознания (день рождения)"""
        # Число сознания: сумма цифр дня до одной цифры
        def get_number(day):
            while day > 9:
                day = sum(int(d) for d in str(day))
            return day
            
        n1 = get_number(d1.day)
        n2 = get_number(d2.day)
        
        # Матрица совместимости (примерная)
        # Одинаковые числа часто понимают друг друга (80%)
        # Разные - по разному
        if n1 == n2: return 90
        if abs(n1 - n2) in [3, 4, 6]: return 85 # Гармония
        return 65 # Средне

    def _calc_matrix_compatibility(self, d1: datetime, d2: datetime) -> int:
        """Совместимость по матрице (упрощенно)"""
        # Обычно считают общие арканы.
        # Для MVP сделаем заглушку на основе разницы дат (чем ближе или гармоничнее, тем лучше)
        diff_days = abs((d1 - d2).days)
        if diff_days < 365: return 95 # Ровесники
        if diff_days % 365 < 30: return 80 # Близко по сезону
        return 70

    def _calc_biorhythm(self, d1: datetime, d2: datetime) -> int:
        """Псевдо-расчет по биоритмам (симуляция)"""
        # Используем хэш дат для детерминированного но "случайного" результата
        seed = d1.toordinal() + d2.toordinal()
        random.seed(seed)
        return random.randint(50, 100)

    def _generate_report(self, score: int) -> str:
        if score > 85:
            return "🔥 *Идеальная пара!* Вы понимаете друг друга с полуслова. Ваши энергии резонируют на высшем уровне."
        elif score > 65:
            return "✨ *Отличная совместимость.* Есть над чем работать, но фундамент крепкий. Уважайте различия друг друга."
        else:
            return "🌪 *Кармический союз.* Вас ждут уроки и испытания. Чтобы быть вместе, нужно много терпения и мудрости."

compatibility = CompatibilityCalculator()
