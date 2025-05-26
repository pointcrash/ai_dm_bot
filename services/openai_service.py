from openai import AsyncOpenAI
from config.config import OPENAI_API_KEY, MAIN_OPENAI_MODEL, MAIN_OPENAI_TEMPERATURE
from services.history_service import HistoryService
from services.logger_service import LoggerService
from services.character_service import CharacterService

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.model = MAIN_OPENAI_MODEL
        self.temperature = MAIN_OPENAI_TEMPERATURE
        self.history_service = HistoryService()
        # self.logger_service = LoggerService()
        self.character_service = CharacterService()

    async def get_response(self, user_id: int, user_message: str, chat_id: int = None) -> str:
        # Если chat_id не указан, используем user_id как chat_id для личных сообщений
        if chat_id is None:
            chat_id = user_id

        # Получаем информацию об активном персонаже пользователя
        active_character = self.character_service.get_active_character(user_id)
        character_info = ""
        
        if active_character:
            character_info = f"\n\nИнформация о персонаже пользователя:\n"
            character_info += f"Имя: {active_character['name']}\n"

        result_message = f"User ID: {str(user_id)}"
        if character_info:
            result_message += character_info

        result_message += f"\n\nИгрок написал: {user_message}"

        # Добавляем сообщение пользователя в историю
        self.history_service.add_user_message(chat_id, result_message)
        
        # Получаем историю диалога
        messages = self.history_service.get_messages_for_api(chat_id)
        
        # Логируем запрос
        # self.logger_service.log_request(user_id, messages)
        
        # Получаем ответ от OpenAI
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        
        # Сохраняем ответ ассистента в историю
        assistant_response = response.choices[0].message.content
        self.history_service.add_assistant_message(chat_id, assistant_response)
        
        return assistant_response 