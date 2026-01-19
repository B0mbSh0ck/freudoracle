
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Mock aiohttp
from unittest.mock import MagicMock
sys.modules['aiohttp'] = MagicMock()
sys.modules['bs4'] = MagicMock()

from oracle.horoscope.horoscope_parser import horoscope_parser

def test_dates():
    test_cases = [
        (21, 3, "aries"),
        (20, 4, "aries"), # End ofARIES
        (21, 4, "taurus"),
        (1, 1, "capricorn"),
        # Boundary cases
        (20, 3, "pisces"),
        (19, 2, "pisces"),
        (18, 2, "aquarius"),
    ]
    
    print("Testing get_sign_from_date...")
    for day, month, expected in test_cases:
        result = horoscope_parser.get_sign_from_date(day, month)
        status = "✅" if result == expected else f"❌ (Expected {expected})"
        print(f"{day}.{month} -> {result} {status}")

    print("\nTesting fallback for invalid result (manual check):")
    # Simulate what happens if None is passed (though types say int)
    try:
        print(f"None, None -> {horoscope_parser.get_sign_from_date(None, None)}")
    except Exception as e:
        print(f"None, None -> Error: {e}")

if __name__ == "__main__":
    test_dates()
