"""
Модуль натальной карты
Расчет полной астрологической карты рождения
"""
import swisseph as swe
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple
import pytz


@dataclass
class NatalPlanet:
    """Планета в натальной карте"""
    name: str
    longitude: float
    sign: str
    house: int
    degree: int
    minute: int
    retrograde: bool
    element: str  # fire, earth, air, water
    quality: str  # cardinal, fixed, mutable


@dataclass
class NatalAspect:
    """Аспект между планетами"""
    planet1: str
    planet2: str
    aspect_type: str  # conjunction, opposition, trine, square, sextile
    orb: float
    interpretation: str


@dataclass
class NatalChart:
    """Натальная карта"""
    birth_date: datetime
    latitude: float
    longitude: float
    location: str
    
    # Основные точки
    ascendant: float
    mc: float  # Midheaven
    descendant: float
    ic: float  # Imum Coeli
    
    # Планеты
    planets: Dict[str, NatalPlanet]
    
    # Дома
    houses: List[float]
    
    # Аспекты
    aspects: List[NatalAspect]
    
    # Элементы и качества
    element_balance: Dict[str, int]
    quality_balance: Dict[str, int]
    
    # Доминирующий знак
    dominant_sign: str
    dominant_element: str
    
    # Интерпретация
    sun_sign: str
    moon_sign: str
    rising_sign: str
    chart_type: str  # bundle, bowl, bucket, locomotive, etc.


class NatalAstrology:
    """Расчет натальной карты"""
    
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
        'Pluto': swe.PLUTO,
        'North Node': swe.TRUE_NODE,
        'Chiron': swe.CHIRON
    }
    
    SIGNS = [
        'Овен', 'Телец', 'Близнецы', 'Рак',
        'Лев', 'Дева', 'Весы', 'Скорпион',
        'Стрелец', 'Козерог', 'Водолей', 'Рыбы'
    ]
    
    ELEMENTS = {
        'Овен': 'fire', 'Лев': 'fire', 'Стрелец': 'fire',
        'Телец': 'earth', 'Дева': 'earth', 'Козерог': 'earth',
        'Близнецы': 'air', 'Весы': 'air', 'Водолей': 'air',
        'Рак': 'water', 'Скорпион': 'water', 'Рыбы': 'water'
    }
    
    QUALITIES = {
        'Овен': 'cardinal', 'Рак': 'cardinal', 'Весы': 'cardinal', 'Козерог': 'cardinal',
        'Телец': 'fixed', 'Лев': 'fixed', 'Скорпион': 'fixed', 'Водолей': 'fixed',
        'Близнецы': 'mutable', 'Дева': 'mutable', 'Стрелец': 'mutable', 'Рыбы': 'mutable'
    }
    
    def __init__(self):
        swe.set_ephe_path(None)
    
    def calculate_natal_chart(
        self, 
        birth_date: datetime,
        latitude: float,
        longitude: float,
        location: str = "Unknown"
    ) -> NatalChart:
        """Рассчитать натальную карту"""
        
        # Конвертируем в Julian Day
        jd = swe.julday(
            birth_date.year, birth_date.month, birth_date.day,
            birth_date.hour + birth_date.minute/60.0 + birth_date.second/3600.0
        )
        
        # Рассчитываем планеты
        planets = {}
        for name, planet_id in self.PLANETS.items():
            try:
                position = swe.calc_ut(jd, planet_id)[0]
                lon = position[0]
                speed = position[3]
                
                sign = self._get_sign(lon)
                degree = int(lon % 30)
                minute = int((lon % 1) * 60)
                
                planets[name] = NatalPlanet(
                    name=name,
                    longitude=lon,
                    sign=sign,
                    house=0,  # Будет рассчитан позже
                    degree=degree,
                    minute=minute,
                    retrograde=(speed < 0),
                    element=self.ELEMENTS.get(sign, 'unknown'),
                    quality=self.QUALITIES.get(sign, 'unknown')
                )
            except:
                continue
        
        # Рассчитываем дома
        houses_cusps = swe.houses(jd, latitude, longitude, b'P')[0]
        ascendant = houses_cusps[0]
        mc = houses_cusps[9]
        descendant = (ascendant + 180) % 360
        ic = (mc + 180) % 360
        
        # Определяем дома для планет
        for planet in planets.values():
            planet.house = self._get_house(planet.longitude, houses_cusps)
        
        # Рассчитываем аспекты
        aspects = self._calculate_aspects(planets)
        
        # Балансы элементов и качеств
        element_balance = self._calculate_element_balance(planets)
        quality_balance = self._calculate_quality_balance(planets)
        
        # Определяем доминирующие
        dominant_element = max(element_balance, key=element_balance.get)
        dominant_sign = planets['Sun'].sign
        
        # Тип карты
        chart_type = self._determine_chart_type(planets)
        
        return NatalChart(
            birth_date=birth_date,
            latitude=latitude,
            longitude=longitude,
            location=location,
            ascendant=ascendant,
            mc=mc,
            descendant=descendant,
            ic=ic,
            planets=planets,
            houses=list(houses_cusps),
            aspects=aspects,
            element_balance=element_balance,
            quality_balance=quality_balance,
            dominant_sign=dominant_sign,
            dominant_element=dominant_element,
            sun_sign=planets['Sun'].sign,
            moon_sign=planets['Moon'].sign,
            rising_sign=self._get_sign(ascendant),
            chart_type=chart_type
        )
    
    def _get_sign(self, longitude: float) -> str:
        """Получить знак зодиака"""
        sign_index = int(longitude / 30)
        return self.SIGNS[sign_index]
    
    def _get_house(self, planet_lon: float, houses: List[float]) -> int:
        """Определить дом планеты"""
        for i in range(12):
            next_house = (i + 1) % 12
            house_start = houses[i]
            house_end = houses[next_house]
            
            if house_end < house_start:
                if planet_lon >= house_start or planet_lon < house_end:
                    return i + 1
            else:
                if house_start <= planet_lon < house_end:
                    return i + 1
        return 1
    
    def _calculate_aspects(self, planets: Dict[str, NatalPlanet]) -> List[NatalAspect]:
        """Рассчитать аспекты между планетами"""
        aspects = []
        aspect_types = {
            0: ('conjunction', 8, 'Соединение - слияние энергий'),
            60: ('sextile', 6, 'Секстиль - гармоничная возможность'),
            90: ('square', 8, 'Квадрат - напряжение и вызов'),
            120: ('trine', 8, 'Трин - гармония и поток'),
            180: ('opposition', 8, 'Оппозиция - противостояние и баланс')
        }
        
        planet_list = list(planets.items())
        for i, (name1, planet1) in enumerate(planet_list):
            for name2, planet2 in planet_list[i+1:]:
                angle = abs(planet1.longitude - planet2.longitude)
                if angle > 180:
                    angle = 360 - angle
                
                for aspect_angle, (asp_type, orb, interp) in aspect_types.items():
                    if abs(angle - aspect_angle) <= orb:
                        aspects.append(NatalAspect(
                            planet1=name1,
                            planet2=name2,
                            aspect_type=asp_type,
                            orb=abs(angle - aspect_angle),
                            interpretation=interp
                        ))
                        break
        
        return aspects
    
    def _calculate_element_balance(self, planets: Dict[str, NatalPlanet]) -> Dict[str, int]:
        """Рассчитать баланс элементов"""
        balance = {'fire': 0, 'earth': 0, 'air': 0, 'water': 0}
        for planet in planets.values():
            if planet.element in balance:
                balance[planet.element] += 1
        return balance
    
    def _calculate_quality_balance(self, planets: Dict[str, NatalPlanet]) -> Dict[str, int]:
        """Рассчитать баланс качеств"""
        balance = {'cardinal': 0, 'fixed': 0, 'mutable': 0}
        for planet in planets.values():
            if planet.quality in balance:
                balance[planet.quality] += 1
        return balance
    
    def _determine_chart_type(self, planets: Dict[str, NatalPlanet]) -> str:
        """Определить тип карты (Jones patterns)"""
        # Упрощенная версия
        positions = sorted([p.longitude for p in planets.values()])
        
        # Проверяем есть ли все планеты в пределах 180 градусов
        max_gap = 0
        for i in range(len(positions)):
            gap = (positions[(i+1)%len(positions)] - positions[i]) % 360
            max_gap = max(max_gap, gap)
        
        if max_gap > 180:
            return "Bowl (Чаша)"
        elif max_gap > 120:
            return "Bucket (Ведро)"
        else:
            return "Bundle (Связка)"
    
    def format_natal_chart(self, chart: NatalChart) -> str:
        """Форматировать натальную карту для отображения"""
        result = f"""
🌟 **НАТАЛЬНАЯ КАРТА**

**Дата рождения:** {chart.birth_date.strftime('%d.%m.%Y %H:%M')}
**Место:** {chart.location}

**☀️ ОСНОВЫ:**
• Солнце: {chart.sun_sign} (личность, эго)
• Луна: {chart.moon_sign} (эмоции, подсознание)
• Асцендент: {chart.rising_sign} (внешность, первое впечатление)

**🌍 БАЛАНС ЭЛЕМЕНТОВ:**
• 🔥 Огонь: {chart.element_balance.get('fire', 0)} планет
• 🌍 Земля: {chart.element_balance.get('earth', 0)} планет
• 💨 Воздух: {chart.element_balance.get('air', 0)} планет
• 💧 Вода: {chart.element_balance.get('water', 0)} планет

**Доминирующий элемент:** {chart.dominant_element.upper()}

**📍 ПЛАНЕТЫ В ЗНАКАХ:**
"""
        
        for name, planet in chart.planets.items():
            retro = "℞" if planet.retrograde else ""
            result += f"• {name}: {planet.degree}°{planet.minute:02d}' {planet.sign} ({planet.house}-й дом) {retro}\n"
        
        result += f"\n**🔗 ОСНОВНЫЕ АСПЕКТЫ:**\n"
        for aspect in chart.aspects[:10]:  # Показываем топ-10 аспектов
            result += f"• {aspect.planet1} {aspect.aspect_type} {aspect.planet2} ({aspect.interpretation})\n"
        
        result += f"\n**📊 ТИП КАРТЫ:** {chart.chart_type}"
        
        return result.strip()


# Singleton
natal_astrology = NatalAstrology()
