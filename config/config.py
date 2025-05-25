import os
from dotenv import load_dotenv
from config.adventure_promt import EASY_ADVENTURE_PROMT

# Загружаем переменные окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Конфигурация OpenAI
OPENAI_API_KEY = os.getenv("MY_PERSONAL_OPENAI_API_KEY")
MAIN_OPENAI_MODEL = "gpt-4o-mini" 
MAIN_OPENAI_TEMPERATURE = 0.7
SUMMARY_OPENAI_MODEL = "gpt-4o-mini"
SUMMARY_OPENAI_TEMPERATURE = 0.3

MAX_HISTORY_LENGTH = 20
MAIN_PROMT = EASY_ADVENTURE_PROMT