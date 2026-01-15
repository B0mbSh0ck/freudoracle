"""
Бесплатные AI альтернативы для снижения затрат
"""
import aiohttp
import asyncio
from typing import Optional


class FreeAIProviders:
    """Бесплатные AI провайдеры"""
    
    @staticmethod
    async def groq_completion(prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Groq API - бесплатный доступ к Llama, Mixtral и другим моделям
        https://console.groq.com/
        
        БЕСПЛАТНО: До 14,400 запросов в день!
        """
        api_key = "YOUR_GROQ_API_KEY"  # Получить на https://console.groq.com/
        
        if not api_key or api_key == "YOUR_GROQ_API_KEY":
            return None
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama3-70b-8192",  # Или mixtral-8x7b-32768
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 400
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Groq API error: {e}")
        
        return None
    
    @staticmethod
    async def together_completion(prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Together AI - бесплатные $25 кредитов при регистрации
        https://api.together.xyz/
        
        Модели: Llama-3, Mixtral, и другие open-source модели
        """
        api_key = "YOUR_TOGETHER_API_KEY"
        
        if not api_key or api_key == "YOUR_TOGETHER_API_KEY":
            return None
        
        url = "https://api.together.xyz/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "meta-llama/Llama-3-70b-chat-hf",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 400
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Together AI error: {e}")
        
        return None
    
    @staticmethod
    async def huggingface_completion(prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        HuggingFace Inference API - БЕСПЛАТНО для многих моделей
        https://huggingface.co/inference-api
        
        Rate limit: Зависит от модели, но обычно достаточно для малых проектов
        """
        api_key = "YOUR_HF_API_KEY"
        
        if not api_key or api_key == "YOUR_HF_API_KEY":
            return None
        
        # Используем бесплатную модель
        url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        data = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 400,
                "temperature": 0.8,
                "return_full_text": False
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0:
                            return result[0].get('generated_text', '')
        except Exception as e:
            print(f"HuggingFace API error: {e}")
        
        return None


# Вспомогательные функции для настройки

def get_free_ai_config():
    """Получить конфигурацию для бесплатных AI"""
    return """
# БЕСПЛАТНЫЕ AI АЛЬТЕРНАТИВЫ (добавьте в .env):

# 1. Groq (РЕКОМЕНДУЕТСЯ - очень быстро и бесплатно)
# Регистрация: https://console.groq.com/
# Лимит: 14,400 запросов/день БЕСПЛАТНО
GROQ_API_KEY=your_groq_api_key

# 2. Together AI
# Регистрация: https://api.together.xyz/
# Бонус: $25 при регистрации
TOGETHER_API_KEY=your_together_api_key

# 3. HuggingFace
# Регистрация: https://huggingface.co/
# Лимит: Зависит от модели
HUGGINGFACE_API_KEY=your_hf_api_key

# Приоритет использования:
# 1. Пробуем Groq (быстро, бесплатно)
# 2. Если не работает -> OpenAI/Anthropic (платно)
"""


# Пример использования
async def test_free_apis():
    """Тест бесплатных API"""
    prompt = "Ответь коротко: что такое счастье?"
    system = "Ты - мудрый философ."
    
    print("Тестируем Groq...")
    result = await FreeAIProviders.groq_completion(prompt, system)
    if result:
        print(f"✓ Groq: {result[:100]}...")
    else:
        print("✗ Groq не настроен")
    
    print("\nТестируем Together AI...")
    result = await FreeAIProviders.together_completion(prompt, system)
    if result:
        print(f"✓ Together: {result[:100]}...")
    else:
        print("✗ Together не настроен")
    
    print("\nТестируем HuggingFace...")
    result = await FreeAIProviders.huggingface_completion(prompt, system)
    if result:
        print(f"✓ HuggingFace: {result[:100]}...")
    else:
        print("✗ HuggingFace не настроен")


if __name__ == "__main__":
    # Запустить тест
    asyncio.run(test_free_apis())
