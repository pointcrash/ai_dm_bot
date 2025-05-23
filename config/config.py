import os
from dotenv import load_dotenv
from config.adventure_promt import RUSSIAN_ADVENTURE_PROMT

# Загружаем переменные окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Конфигурация OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_FROM_WORK")
MAIN_OPENAI_MODEL = "gpt-3.5-turbo" 
MAIN_OPENAI_TEMPERATURE = 0.7
SUMMARY_OPENAI_MODEL = "gpt-4o-mini"
SUMMARY_OPENAI_TEMPERATURE = 0.3

MAX_HISTORY_LENGTH = 20
MAIN_PROMT = RUSSIAN_ADVENTURE_PROMT