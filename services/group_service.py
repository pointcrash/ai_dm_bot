from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class GroupMember:
    user_id: int
    character_name: str
    joined_at: datetime = field(default_factory=datetime.now)

@dataclass
class Group:
    members: List[GroupMember] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class GroupService:
    def __init__(self):
        self.groups: Dict[int, Group] = {}  # chat_id -> Group

    def get_group(self, chat_id: int) -> Group:
        if chat_id not in self.groups:
            self.groups[chat_id] = Group()
        return self.groups[chat_id]

    def add_member(self, chat_id: int, user_id: int, character_name: str) -> bool:
        group = self.get_group(chat_id)
        
        # Проверяем, не состоит ли уже персонаж в группе
        if any(member.character_name == character_name for member in group.members):
            return False
            
        group.members.append(GroupMember(user_id=user_id, character_name=character_name))
        group.updated_at = datetime.now()
        return True

    def remove_member(self, chat_id: int, character_name: str) -> bool:
        group = self.get_group(chat_id)
        
        # Находим и удаляем участника
        for i, member in enumerate(group.members):
            if member.character_name == character_name:
                group.members.pop(i)
                group.updated_at = datetime.now()
                return True
        return False

    def get_members(self, chat_id: int) -> List[GroupMember]:
        group = self.get_group(chat_id)
        return group.members

    def get_formatted_members(self, chat_id: int) -> str:
        members = self.get_members(chat_id)
        if not members:
            return "В группе пока нет участников"
            
        formatted = "👥 Состав группы:\n\n"
        for member in members:
            formatted += f"• {member.character_name}\n"
        return formatted 