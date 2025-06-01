from openai import AsyncOpenAI
from config.config import OPENAI_API_KEY, MAIN_OPENAI_MODEL, MAIN_OPENAI_TEMPERATURE
from services.history_service import HistoryService
from services.logger_service import LoggerService
from services.character_service import CharacterService
from services.usage_service import UsageService
from services.log_token_usage_service import TokenUsageService
from services.group_service import GroupService


class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.model = MAIN_OPENAI_MODEL
        self.temperature = MAIN_OPENAI_TEMPERATURE
        self.history_service = HistoryService()
        self.logger_service = LoggerService()
        self.character_service = CharacterService()
        self.usage_service = UsageService()
        self.token_usage_service = TokenUsageService()
        self.group_service = GroupService()

    async def get_response(self, user_id: int, user_message: str, chat_id: int = None) -> str:
        # Если chat_id не указан, используем user_id как chat_id для личных сообщений
        if chat_id is None:
            chat_id = user_id

        # Проверяем доступность запросов
        can_use, _ = self.usage_service.decrement_usage(user_id)
        if not can_use:
            return f"❌ У вас закончились доступные запросы к нейросети."

        # Получаем информацию об активном персонаже пользователя
        active_character = self.character_service.get_active_character(user_id)

        if not active_character:
            return "❌ У вас нет активного персонажа. Сначала создайте и активируйте персонажа."

        # Проверяем, состоит ли персонаж в группе
        if not self.group_service.is_member_in_group(chat_id, active_character['name']):
            return f"❌ Ваш персонаж {active_character['name']} не состоит в группе. Используйте /join чтобы присоединиться."

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
        self.logger_service.log_request(user_id, messages)
        
        # Получаем ответ от OpenAI
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        
        # Сохраняем ответ ассистента в историю
        assistant_response = response.choices[0].message.content
        self.history_service.add_assistant_message(chat_id, assistant_response)
        
        # Логируем использование токенов
        usage_info = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        self.token_usage_service.log_token_usage(chat_id, usage_info)
        
        return assistant_response 