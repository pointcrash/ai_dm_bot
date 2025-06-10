import json
from pathlib import Path
from typing import Dict, Optional

class ChatSettingsService:
    def __init__(self, settings_dir: str = "data/chat_settings"):
        self.settings_dir = Path(settings_dir)
        self._ensure_settings_dir()

    def _ensure_settings_dir(self):
        """Создает директорию для хранения настроек чата"""
        self.settings_dir.mkdir(parents=True, exist_ok=True)

    def _get_settings_file_path(self) -> Path:
        """Возвращает путь к файлу с настройками чата"""
        return self.settings_dir / "chat_settings.json"

    def _read_settings_data(self) -> Dict:
        """Читает настройки чата из файла"""
        settings_file = self._get_settings_file_path()
        if not settings_file.exists():
            return {}
            
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Преобразуем строковые ключи в целые числа
                return {int(k): v for k, v in data.items()}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении настроек чата: {e}")
            return {}

    def _write_settings_data(self, data: Dict):
        """Записывает настройки чата в файл"""
        try:
            with open(self._get_settings_file_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка при записи настроек чата: {e}")

    def get_chat_settings(self, chat_id: int) -> Dict:
        """Возвращает настройки чата"""
        data = self._read_settings_data()
        if chat_id not in data:
            data[chat_id] = {
                "voice_enabled": False
            }
            self._write_settings_data(data)
        return data[chat_id]

    def toggle_voice(self, chat_id: int) -> bool:
        """Переключает режим голосовых ответов"""
        data = self._read_settings_data()
        if chat_id not in data:
            data[chat_id] = {"voice_enabled": True}
        else:
            data[chat_id]["voice_enabled"] = not data[chat_id].get("voice_enabled", False)
        self._write_settings_data(data)
        return data[chat_id]["voice_enabled"]

    def is_voice_enabled(self, chat_id: int) -> bool:
        """Проверяет, включен ли режим голосовых ответов"""
        settings = self.get_chat_settings(chat_id)
        return settings.get("voice_enabled", False) 