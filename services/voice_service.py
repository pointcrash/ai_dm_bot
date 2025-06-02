from openai import OpenAI
from config.config import OPENAI_API_KEY, TRANSCRIBE_MODEL
import os
import tempfile
from aiogram.types import Voice

class VoiceService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
    async def transcribe_voice(self, voice: Voice) -> str:
        """
        Преобразует голосовое сообщение в текст с помощью Whisper API
        """
        # Создаем временный файл для сохранения голосового сообщения
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Скачиваем голосовое сообщение
            voice_file = await voice.bot.get_file(voice.file_id)
            await voice.bot.download_file(voice_file.file_path, temp_path)
            
            # Открываем файл и отправляем в Whisper API
            with open(temp_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=TRANSCRIBE_MODEL,
                    file=audio_file
                )
                
            return transcript.text
            
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path) 