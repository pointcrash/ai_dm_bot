import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from config.config import DEFAULT_REQUESTS_LIMIT

class UsageService:
    def __init__(self, usage_dir: str = "data/usage"):
        self.usage_dir = Path(usage_dir)
        self._ensure_usage_dir()

    def _ensure_usage_dir(self):
        """Создает директорию для хранения данных об использовании"""
        self.usage_dir.mkdir(parents=True, exist_ok=True)

    def _get_usage_file_path(self) -> Path:
        """Возвращает путь к файлу с данными об использовании"""
        return self.usage_dir / "usage_stats.json"

    def _read_usage_data(self) -> Dict:
        """Читает данные об использовании из файла"""
        usage_file = self._get_usage_file_path()
        if not usage_file.exists():
            return {}
            
        try:
            with open(usage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Преобразуем строковые ключи в целые числа
                return {int(k): v for k, v in data.items()}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении данных об использовании: {e}")
            return {}

    def _write_usage_data(self, data: Dict):
        """Записывает данные об использовании в файл"""
        try:
            with open(self._get_usage_file_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка при записи данных об использовании: {e}")

    def update_user_info(self, user_id: int, first_name: Optional[str] = None, username: Optional[str] = None):
        """
        Обновляет информацию о пользователе
        
        Args:
            user_id (int): ID пользователя
            first_name (Optional[str]): Имя пользователя
            username (Optional[str]): Ник пользователя
        """
        data = self._read_usage_data()
        
        if user_id not in data:
            data[user_id] = {
                "remaining_requests": DEFAULT_REQUESTS_LIMIT,
                "last_request": None,
                "total_requests": 0,
                "first_name": None,
                "username": None
            }
        
        if first_name:
            data[user_id]["first_name"] = first_name
        if username:
            data[user_id]["username"] = username
            
        self._write_usage_data(data)

    def decrement_usage(self, user_id: int) -> Tuple[bool, int]:
        """
        Уменьшает количество доступных запросов для пользователя.
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            Tuple[bool, int]: (можно ли использовать нейросеть, оставшееся количество запросов)
        """
        data = self._read_usage_data()
        
        # Инициализируем данные для пользователя, если их еще нет
        if user_id not in data:
            data[user_id] = {
                "remaining_requests": DEFAULT_REQUESTS_LIMIT,
                "last_request": None,
                "total_requests": 0,
                "first_name": None,
                "username": None
            }
        
        # Проверяем, есть ли еще доступные запросы
        if data[user_id]["remaining_requests"] <= 0:
            return False, 0
            
        # Уменьшаем счетчик и обновляем время последнего запроса
        data[user_id]["remaining_requests"] -= 1
        data[user_id]["total_requests"] += 1
        data[user_id]["last_request"] = datetime.now().isoformat()
        
        # Сохраняем обновленные данные
        self._write_usage_data(data)
        
        return True, data[user_id]["remaining_requests"]

    def get_usage_stats(self, user_id: int) -> Optional[Dict]:
        """Возвращает статистику использования для пользователя"""
        data = self._read_usage_data()
        return data.get(user_id)

    def get_formatted_usage_stats(self, user_id: int) -> str:
        """Возвращает отформатированную статистику использования"""
        stats = self.get_usage_stats(user_id)
        if not stats:
            return f"Статистика использования несформирована\nБесплатных запросов: {DEFAULT_REQUESTS_LIMIT}"
            
        last_request = datetime.fromisoformat(stats["last_request"]) if stats["last_request"] else None
        last_request_str = last_request.strftime("%d.%m.%Y %H:%M:%S") if last_request else "Нет данных"
        
        user_info = []
        if stats.get("first_name"):
            user_info.append(f"Имя: {stats['first_name']}")
        if stats.get("username"):
            user_info.append(f"Ник: @{stats['username']}")
        user_info_str = "\n".join(user_info) if user_info else "Информация о пользователе отсутствует"
        
        return f"📊 Статистика использования:\n" \
               f"{user_info_str}\n" \
               f"Осталось запросов: {stats['remaining_requests']}\n" \
               f"Всего сделано запросов: {stats.get('total_requests', 0)}\n" \
               f"Последний запрос: {last_request_str}" 