"""
Модуль хорарной астрологии
Анализ вопроса по времени его задания
"""
import swisseph as swe
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List
import pytz


@dataclass
class Planet:
    """Планета в гороскопе"""
    name: str
    longitude: float  # Эклиптическая долгота
    sign: str
    house: int
    retrograde: bool


@dataclass
class HoraryChart:
    """Хорарная карта"""
    question_time: datetime
    ascendant: float
    mc: float  # Midheaven
    planets: Dict[str, Planet]
    houses: List[float]
    interpretation: str


class HoraryAstrology:
    """Хорарная астрология"""
    
    # Планеты
    PLANETS = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mercury': swe.MERCURY,
        'Venus': swe.VENUS,
        'Mars': swe.MARS,
        'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN,
        'Uranus': swe.URANUS,
        'Neptune': swe.NEPTUNE,
        'Pluto': swe.PLUTO
    }
    
    # Знаки зодиака
    SIGNS = [
        'Овен', 'Телец', 'Близнецы', 'Рак',
        'Лев', 'Дева', 'Весы', 'Скорпион',
        'Стрелец', 'Козерог', 'Водолей', 'Рыбы'
    ]
    
    def __init__(self):
        # Устанавливаем путь к эфемеридам Swiss Ephemeris
        # В продакшене нужно будет скачать файлы эфемерид
        swe.set_ephe_path(None)  # Использует встроенные данные
    
    def calculate_chart(self, dt: datetime, latitude: float = 55.75, longitude: float = 37.62) -> HoraryChart:
        """
        Рассчитать хорарную карту
        
        Args:
            dt: Время вопроса
            latitude: Широта места (по умолчанию Москва)
            longitude: Долгота места (по умолчанию Москва)
        """
        # Преобразуем время в Julian Day
        jd = swe.julday(dt.year, dt.month, dt.day, 
                       dt.hour + dt.minute/60.0 + dt.second/3600.0)
        
        # Рассчитываем планеты
        planets = {}
        for name, planet_id in self.PLANETS.items():
            position = swe.calc_ut(jd, planet_id)[0]
            lon = position[0]  # Эклиптическая долгота
            speed = position[3]  # Скорость (для определения ретроградности)
            
            planets[name] = Planet(
                name=name,
                longitude=lon,
                sign=self._get_sign(lon),
                house=0,  # Будет рассчитан позже
                retrograde=(speed < 0)
            )
        
        # Рассчитываем дома (система Плацидуса)
        houses_cusps = swe.houses(jd, latitude, longitude, b'P')[0]  # 'P' = Placidus
        ascendant = houses_cusps[0]
        mc = houses_cusps[9]  # 10-й дом (MC)
        
        # Определяем дома для планет
        for planet in planets.values():
            planet.house = self._get_house(planet.longitude, houses_cusps)
        
        # Генерируем базовую интерпретацию
        interpretation = self._interpret_chart(planets, ascendant, mc)
        
        return HoraryChart(
            question_time=dt,
            ascendant=ascendant,
            mc=mc,
            planets=planets,
            houses=list(houses_cusps),
            interpretation=interpretation
        )
    
    def _get_sign(self, longitude: float) -> str:
        """Получить знак зодиака по долготе"""
        sign_index = int(longitude / 30)
        return self.SIGNS[sign_index]
    
    def _get_house(self, planet_lon: float, houses: List[float]) -> int:
        """Определить дом планеты"""
        for i in range(12):
            next_house = (i + 1) % 12
            house_start = houses[i]
            house_end = houses[next_house]
            
            # Учитываем переход через 0 градусов
            if house_end < house_start:
                if planet_lon >= house_start or planet_lon < house_end:
                    return i + 1
            else:
                if house_start <= planet_lon < house_end:
                    return i + 1
        
        return 1  # По умолчанию
    
    def _interpret_chart(self, planets: Dict[str, Planet], ascendant: float, mc: float) -> str:
        """Базовая интерпретация хорарной карты"""
        asc_sign = self._get_sign(ascendant)
        mc_sign = self._get_sign(mc)
        
        # Луна - ключевая планета в хорарной астрологии
        moon = planets['Moon']
        
        interpretation = f"""
**Время вопроса:** определяет момент рождения хорарной карты

**Асцендент в {asc_sign}:**
Показывает, как вы подходите к вопросу и вашу непосредственную реакцию.

**MC в {mc_sign}:**
Указывает на конечную цель или результат ситуации.

**Луна в {moon.sign}, {moon.house}-й дом:**
Луна показывает развитие ситуации. Она в знаке {moon.sign}, что говорит о {"эмоциональной вовлеченности" if moon.sign in ["Рак", "Рыбы", "Скорпион"] else "рациональном подходе"}.
"""
        
        # Проверяем ретроградные планеты
        retrogrades = [p.name for p in planets.values() if p.retrograde]
        if retrogrades:
            interpretation += f"\n**Ретроградные планеты:** {', '.join(retrogrades)}\n"
            interpretation += "Ретроградность указывает на необходимость пересмотра или задержки в соответствующих областях.\n"
        
        return interpretation.strip()
    
    def format_chart(self, chart: HoraryChart) -> str:
        """Форматировать карту для отображения"""
        result = f"""
⭐ **Хорарная карта**
Время вопроса: {chart.question_time.strftime('%Y-%m-%d %H:%M:%S')}

**Асцендент (ASC):** {self._format_degree(chart.ascendant)} {self._get_sign(chart.ascendant)}
**Середина Неба (MC):** {self._format_degree(chart.mc)} {self._get_sign(chart.mc)}

**Планеты:**
"""
        for planet in chart.planets.values():
            retro = " ℞" if planet.retrograde else ""
            result += f"\n{planet.name}: {self._format_degree(planet.longitude)} {planet.sign}, {planet.house}-й дом{retro}"
        
        result += f"\n\n{chart.interpretation}"
        
        return result.strip()
    
    def _format_degree(self, longitude: float) -> str:
        """Форматировать градус"""
        degree = int(longitude % 30)
        minute = int((longitude % 1) * 60)
        return f"{degree}°{minute:02d}'"


# Singleton
horary = HoraryAstrology()
