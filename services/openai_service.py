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
        self.logger_service = LoggerService()
        self.character_service = CharacterService()

    def _format_character_context(self, character: dict) -> str:
        """Format character information into a context string for the AI"""
        context = f"Вы общаетесь с персонажем по имени {character['name']}, "
        context += f"{character['race']} {character['class_name']} {character['level']} уровня. "
        
        # Add character description if available
        if character.get('description'):
            context += f"\nОписание персонажа: {character['description']}\n"
        
        # Add key abilities
        context += "\nОсновные характеристики персонажа:\n"
        for ability, data in character['abilities'].items():
            context += f"- {data['name']}: {data['value']} (модификатор {data['modifier']:+d})\n"
        
        # Add current state
        hp = character['base_stats']['hit_points']
        context += f"\nТекущее состояние:\n"
        context += f"- Здоровье: {hp['current']}/{hp['maximum']} (временные: {hp['temporary']})\n"
        context += f"- Класс брони: {character['base_stats']['armor_class']['value']}\n"
        
        # Add equipment
        context += "\nСнаряжение:\n"
        if character['equipment']['weapons']['items']:
            context += f"- Оружие: {', '.join(character['equipment']['weapons']['items'])}\n"
        if character['equipment']['armor']['items']:
            context += f"- Броня: {', '.join(character['equipment']['armor']['items'])}\n"
        
        # Add spells if character has them
        if character['magic']['spells_known']['cantrips'] or character['magic']['spells_known']['spells']:
            context += "\nЗаклинания:\n"
            if character['magic']['spells_known']['cantrips']:
                context += f"- Заговоры: {', '.join(character['magic']['spells_known']['cantrips'])}\n"
            if character['magic']['spells_known']['spells']:
                context += f"- Известные заклинания: {', '.join(character['magic']['spells_known']['spells'])}\n"
        
        return context

    async def get_response(self, user_id: int, user_message: str) -> str:
        # Добавляем сообщение пользователя в историю
        self.history_service.add_user_message(user_id, user_message)
        
        # Получаем историю диалога
        messages = self.history_service.get_messages_for_api(user_id)
        
        # Получаем активного персонажа
        active_character = self.character_service.get_active_character(user_id)
        
        # Если есть активный персонаж, добавляем его контекст в начало диалога
        if active_character:
            character_context = {
                "role": "system",
                "content": self._format_character_context(active_character)
            }
            messages.insert(len(messages)-1, character_context)
        
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
        self.history_service.add_assistant_message(user_id, assistant_response)
        
        return assistant_response 