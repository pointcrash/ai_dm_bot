import os
from dotenv import load_dotenv
from config.adventure_promt import EASY_ADVENTURE_PROMT
from config.tts_promt import TTS_PROMT

# Загружаем переменные окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Конфигурация OpenAI
OPENAI_API_KEY = os.getenv("MY_PERSONAL_OPENAI_API_KEY")
# Конфигурация OpenAI моделей
MAIN_OPENAI_MODEL = os.getenv("MAIN_OPENAI_MODEL", "gpt-4.1")
MAIN_OPENAI_TEMPERATURE = float(os.getenv("MAIN_OPENAI_TEMPERATURE", "0.7"))
SUMMARY_OPENAI_MODEL = os.getenv("SUMMARY_OPENAI_MODEL", "gpt-4.1") 
SUMMARY_OPENAI_TEMPERATURE = float(os.getenv("SUMMARY_OPENAI_TEMPERATURE", "0.3"))

# Конфигурация использования
DEFAULT_REQUESTS_LIMIT = int(os.getenv("DEFAULT_REQUESTS_LIMIT", "50"))

MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", "10"))
MAIN_PROMT = EASY_ADVENTURE_PROMT

# Конфигурация голосового сервиса
TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "ballad")
TTS_INSTRUCTIONS = TTS_PROMT