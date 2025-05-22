from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from config.config import MAIN_PROMT, MAX_HISTORY_LENGTH
from services.summary_service import SummaryService

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ChatHistory:
    messages: List[Message] = field(default_factory=list)
    max_history: int = MAX_HISTORY_LENGTH
    summary: str = ""

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))
        if len(self.messages) > self.max_history:
            self._create_summary()

    def _create_summary(self):
        # Получаем саммари от SummaryService
        summary_service = SummaryService()
        summary = summary_service.create_summary(self.messages, self.summary)
        
        # Сохраняем саммари
        self.summary = summary
        
        # Очищаем историю
        self.messages.clear()

    def get_messages(self) -> List[dict]:
        messages = []
        if self.summary:
            messages.append({"role": "system", "content": f"Предыдущий контекст диалога: {self.summary}"})
        messages.extend([{"role": msg.role, "content": msg.content} for msg in self.messages])
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
            role = "👤 Вы" if msg.role == "user" else "🤖 Бот"
            formatted += f"{role}: {msg.content}\n\n"
        return formatted

class HistoryService:
    def __init__(self):
        self.chats: Dict[int, ChatHistory] = {}

    def get_chat_history(self, user_id: int) -> ChatHistory:
        if user_id not in self.chats:
            self.chats[user_id] = ChatHistory()
        return self.chats[user_id]

    def add_user_message(self, user_id: int, content: str):
        history = self.get_chat_history(user_id)
        history.add_message("user", content)

    def add_assistant_message(self, user_id: int, content: str):
        history = self.get_chat_history(user_id)
        history.add_message("assistant", content)

    def get_messages_for_api(self, user_id: int) -> List[dict]:
        history = self.get_chat_history(user_id)
        return [{"role": "system", "content": MAIN_PROMT}] + history.get_messages()

    def clear_history(self, user_id: int):
        if user_id in self.chats:
            self.chats[user_id].clear()

    def get_formatted_history(self, user_id: int) -> str:
        history = self.get_chat_history(user_id)
        return history.get_formatted_history() 