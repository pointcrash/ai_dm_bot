import json
import os
from datetime import datetime
from pathlib import Path

class TokenUsageService:
    def __init__(self):
        self.logs_dir = Path("logs/token_usage")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def log_token_usage(self, chat_id: int, usage_info: dict):
        """
        Логирует информацию об использовании токенов для конкретного чата
        """
        log_file = self.logs_dir / f"chat_{chat_id}.json"
        
        # Создаем запись о текущем использовании
        current_usage = {
            "timestamp": datetime.now().isoformat(),
            "prompt_tokens": usage_info["prompt_tokens"],
            "completion_tokens": usage_info["completion_tokens"],
            "total_tokens": usage_info["total_tokens"],
        }
        
        # Читаем существующие логи или создаем новый список
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        else:
            logs = []
        
        # Добавляем новую запись
        logs.append(current_usage)
        
        # Сохраняем обновленные логи
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
            