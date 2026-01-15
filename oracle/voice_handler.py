"""
Модуль обработки голосовых сообщений с использованием Groq Whisper (бесплатно)
"""
import os
import aiohttp
from loguru import logger
import tempfile
from telegram import File as TelegramFile

from config.settings import settings

class VoiceHandler:
    """Обработчик голосовых сообщений"""
    
    @staticmethod
    async def transcribe_audio(file_path: str) -> str | None:
        """
        Транскрибировать аудио файл в текст
        Использует Groq Whisper API (бесплатно) или OpenAI Whisper (платно)
        """
        
        # 1. Пробуем Groq (Бесплатно)
        if settings.groq_api_key or (settings.ai_provider == 'groq' and settings.openai_api_key):
            # Если провайдер groq, но ключ в openai_api_key (наша fallback логика), 
            # то для аудио нам все равно нужен реальный Groq ключ или мы используем прокси url
            
            # Лучше явно проверить наличие ключа Groq
            api_key = settings.groq_api_key
            
            if api_key:
                try:
                    logger.info("🎤 Используем Groq Whisper для транскрипции...")
                    url = "https://api.groq.com/openai/v1/audio/transcriptions"
                    
                    headers = {
                        "Authorization": f"Bearer {api_key}"
                    }
                    
                    # Формируем multipart form data руками или через aiohttp
                    data = aiohttp.FormData()
                    data.add_field('file', open(file_path, 'rb'), filename='voice.ogg')
                    data.add_field('model', 'whisper-large-v3')
                    data.add_field('response_format', 'text')
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers=headers, data=data) as response:
                            if response.status == 200:
                                text = await response.text()
                                return text.strip()
                            else:
                                error_text = await response.text()
                                logger.error(f"Groq Whisper Error: {error_text}")
                except Exception as e:
                    logger.error(f"Ошибка при транскрипции через Groq: {e}")
        
        # 2. Fallback на OpenAI (Платно)
        if settings.openai_api_key:
            try:
                logger.info("🎤 Используем OpenAI Whisper для транскрипции...")
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                
                with open(file_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                    )
                return transcription.text
            except Exception as e:
                logger.error(f"Ошибка при транскрипции через OpenAI: {e}")
                
        return None

voice_handler = VoiceHandler()
