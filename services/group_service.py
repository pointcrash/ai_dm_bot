from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import os
from pathlib import Path
from services.character_service import CharacterService

@dataclass
class GroupMember:
    user_id: int
    character_name: str
    joined_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'character_name': self.character_name,
            'joined_at': self.joined_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            user_id=data['user_id'],
            character_name=data['character_name'],
            joined_at=datetime.fromisoformat(data['joined_at'])
        )

@dataclass
class Group:
    members: List[GroupMember] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'members': [member.to_dict() for member in self.members],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            members=[GroupMember.from_dict(member) for member in data['members']],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )

class GroupService:
    def __init__(self, groups_dir: str = "data/groups"):
        self.groups_dir = Path(groups_dir)
        self.groups: Dict[int, Group] = {}  # chat_id -> Group
        self.character_service = CharacterService()
        self._ensure_groups_dir()
        self._load_groups()

    def _ensure_groups_dir(self):
        """Создает директорию для хранения групп, если она не существует"""
        self.groups_dir.mkdir(parents=True, exist_ok=True)

    def _get_group_file_path(self, chat_id: int) -> Path:
        """Возвращает путь к файлу группы"""
        return self.groups_dir / f"group_{chat_id}.json"

    def _load_groups(self):
        """Загружает все сохраненные группы"""
        for group_file in self.groups_dir.glob("group_*.json"):
            try:
                chat_id = int(group_file.stem.split('_')[1])
                with open(group_file, 'r', encoding='utf-8') as f:
                    group_data = json.load(f)
                    self.groups[chat_id] = Group.from_dict(group_data)
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Ошибка при загрузке группы из файла {group_file}: {e}")

    def _save_group(self, chat_id: int):
        """Сохраняет группу в файл"""
        group = self.groups.get(chat_id)
        if group:
            try:
                with open(self._get_group_file_path(chat_id), 'w', encoding='utf-8') as f:
                    json.dump(group.to_dict(), f, ensure_ascii=False, indent=2)
            except IOError as e:
                print(f"Ошибка при сохранении группы {chat_id}: {e}")

    def get_group(self, chat_id: int) -> Group:
        """Получает группу по ID чата"""
        if chat_id not in self.groups:
            self.groups[chat_id] = Group()
        return self.groups[chat_id]

    def add_member(self, chat_id: int, user_id: int, character_data: Dict[str, Any]) -> bool:
        group = self.get_group(chat_id)
        character_name = character_data['name']
        
        # Проверяем, не состоит ли уже персонаж в группе
        if any(member.character_name == character_name for member in group.members):
            return False
            
        group.members.append(GroupMember(
            user_id=user_id,
            character_name=character_name
        ))
        group.updated_at = datetime.now()
        self._save_group(chat_id)
        return True

    def remove_member(self, chat_id: int, character_name: str) -> bool:
        group = self.get_group(chat_id)
        
        # Находим и удаляем участника
        for i, member in enumerate(group.members):
            if member.character_name == character_name:
                group.members.pop(i)
                group.updated_at = datetime.now()
                self._save_group(chat_id)
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
            character_data = self.character_service.get_active_character(member.user_id)
            if character_data:
                formatted += f"• {character_data['name']} ({character_data['race']} {character_data['class_name']} {character_data['level']} уровня)\n"
            else:
                formatted += f"• {member.character_name} (данные персонажа недоступны)\n"
        return formatted 

    def is_member_in_group(self, chat_id: int, character_name: str) -> bool:
        """Проверяет, состоит ли персонаж в группе"""
        group = self.get_group(chat_id)
        return any(member.character_name == character_name for member in group.members) 