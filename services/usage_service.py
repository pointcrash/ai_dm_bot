import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class UsageService:
    def __init__(self, usage_dir: str = "data/usage"):
        self.usage_dir = Path(usage_dir)
        self.usage_data: Dict[int, Dict] = {}  # user_id -> usage data
        self._ensure_usage_dir()
        self._load_usage_data()

    def _ensure_usage_dir(self):
        """Создает директорию для хранения данных об использовании"""
        self.usage_dir.mkdir(parents=True, exist_ok=True)

    def _get_usage_file_path(self) -> Path:
        """Возвращает путь к файлу с данными об использовании"""
        return self.usage_dir / "usage_stats.json"

    def _load_usage_data(self):
        """Загружает данные об использовании из файла"""
        usage_file = self._get_usage_file_path()
        if usage_file.exists():
            try:
                with open(usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Преобразуем строковые ключи в целые числа
                    self.usage_data = {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка при загрузке данных об использовании: {e}")

    def _save_usage_data(self):
        """Сохраняет данные об использовании в файл"""
        try:
            with open(self._get_usage_file_path(), 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка при сохранении данных об использовании: {e}")

    def increment_usage(self, user_id: int):
        """Увеличивает счетчик использования для пользователя"""
        # Инициализируем данные для пользователя, если их еще нет
        if user_id not in self.usage_data:
            self.usage_data[user_id] = {
                "total_requests": 0,
                "last_request": None
            }
        
        # Увеличиваем счетчик и обновляем время последнего запроса
        self.usage_data[user_id]["total_requests"] += 1
        self.usage_data[user_id]["last_request"] = datetime.now().isoformat()
        
        # Сохраняем обновленные данные
        self._save_usage_data()

    def get_usage_stats(self, user_id: int) -> Optional[Dict]:
        """Возвращает статистику использования для пользователя"""
        return self.usage_data.get(user_id)

    def get_formatted_usage_stats(self, user_id: int) -> str:
        """Возвращает отформатированную статистику использования"""
        stats = self.get_usage_stats(user_id)
        if not stats:
            return "Статистика использования недоступна"
            
        last_request = datetime.fromisoformat(stats["last_request"]) if stats["last_request"] else None
        last_request_str = last_request.strftime("%d.%m.%Y %H:%M:%S") if last_request else "Нет данных"
        
        return f"📊 Статистика использования:\n" \
               f"Всего запросов: {stats['total_requests']}\n" \
               f"Последний запрос: {last_request_str}" 