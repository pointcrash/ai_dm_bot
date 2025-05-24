from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
from config.config import MAIN_PROMT, MAX_HISTORY_LENGTH
from services.summary_service import SummaryService
from services.character_service import CharacterService
from services.group_service import GroupService

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )

@dataclass
class ChatHistory:
    messages: List[Message] = field(default_factory=list)
    max_history: int = MAX_HISTORY_LENGTH
    summary: str = ""

    def add_message(self, role: str, content: str):
        if len(self.messages) >= self.max_history:
            self._create_summary()
        self.messages.append(Message(role=role, content=content))

    def _create_summary(self):
        # Получаем саммари от SummaryService
        summary_service = SummaryService()
        summary = summary_service.create_summary(self.messages, self.summary)
        
        # Сохраняем саммари
        self.summary = summary
        
        # Очищаем историю
        self.messages.clear()

    def get_messages(self) -> List[dict]:
        messages = [{"role": msg.role, "content": msg.content} for msg in self.messages]
        return messages

    def clear(self):
        self.messages.clear()
        self.summary = ""

    def get_formatted_history(self) -> str:
        if not self.messages and not self.summary:
            return "История диалога пуста"
        
        formatted = "📜 История диалога:\n\n"
        if self.summary:
            formatted += f"📝 Контекст: {self.summary}\n\n"
        for msg in self.messages:
            role = "Вы" if msg.role == "user" else "Мастер подземелий"
            formatted += f"{role}: {msg.content}\n\n"
        return formatted

    def to_dict(self):
        return {
            'messages': [msg.to_dict() for msg in self.messages],
            'summary': self.summary
        }

    @classmethod
    def from_dict(cls, data: dict):
        history = cls()
        history.messages = [Message.from_dict(msg_data) for msg_data in data['messages']]
        history.summary = data['summary']
        return history

class HistoryService:
    def __init__(self, history_dir: str = "data/history"):
        self.history_dir = Path(history_dir)
        self.chats: Dict[int, ChatHistory] = {}  # chat_id -> ChatHistory
        self.character_service = CharacterService()
        self.group_service = GroupService()
        self._ensure_history_dir()
        self._load_histories()

    def _ensure_history_dir(self):
        """Создает директорию для хранения истории, если она не существует"""
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _get_history_file_path(self, chat_id: int) -> Path:
        """Возвращает путь к файлу истории"""
        return self.history_dir / f"chat_{chat_id}.json"

    def _load_histories(self):
        """Загружает все сохраненные истории"""
        for history_file in self.history_dir.glob("chat_*.json"):
            try:
                chat_id = int(history_file.stem.split('_')[1])
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    self.chats[chat_id] = ChatHistory.from_dict(history_data)
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Ошибка при загрузке истории из файла {history_file}: {e}")

    def _save_history(self, chat_id: int):
        """Сохраняет историю в файл"""
        history = self.chats.get(chat_id)
        if history:
            try:
                with open(self._get_history_file_path(chat_id), 'w', encoding='utf-8') as f:
                    json.dump(history.to_dict(), f, ensure_ascii=False, indent=2)
            except IOError as e:
                print(f"Ошибка при сохранении истории {chat_id}: {e}")

    def _format_character_context(self, character: dict) -> str:
        """Format character information into a context string for the AI"""
        context = f"Персонаж пользователя с id {character['user_id']} по имени {character['name']}, "
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

    def _format_group_context(self, chat_id: int) -> str:
        """Format group information into a context string for the AI"""
        members = self.group_service.get_members(chat_id)
        if not members:
            return ""
            
        context = "\n👥 Состав группы:\n"
        for member in members:
            char_data = member.character_data
            context += f"\n{self._format_character_context(char_data)}"
        return context

    def get_chat_history(self, chat_id: int) -> ChatHistory:
        if chat_id not in self.chats:
            self.chats[chat_id] = ChatHistory()
        return self.chats[chat_id]

    def add_user_message(self, chat_id: int, content: str):
        history = self.get_chat_history(chat_id)
        history.add_message("user", content)
        self._save_history(chat_id)

    def add_assistant_message(self, chat_id: int, content: str):
        history = self.get_chat_history(chat_id)
        history.add_message("assistant", content)
        self._save_history(chat_id)

    def get_messages_for_api(self, chat_id: int) -> List[dict]:
        history = self.get_chat_history(chat_id)
        
        # Формируем единое system-сообщение
        system_content = MAIN_PROMT
        
        # Добавляем саммари, если есть
        if history.summary:
            system_content += f"\n\nПредыдущий контекст диалога: {history.summary}"
            
        # Перезагружаем информацию о группе перед каждым запросом
        self.group_service._load_groups()
        group_context = self._format_group_context(chat_id)
        if group_context:
            system_content += group_context
            
        return [{"role": "system", "content": system_content}] + history.get_messages()

    def clear_history(self, chat_id: int):
        if chat_id in self.chats:
            self.chats[chat_id].clear()
            self._save_history(chat_id)

    def get_formatted_history(self, chat_id: int) -> str:
        history = self.get_chat_history(chat_id)
        return history.get_formatted_history() 