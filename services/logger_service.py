import json
import logging
from datetime import datetime
from pathlib import Path

class LoggerService:
    def __init__(self):
        # Создаем директорию для логов если её нет
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Настраиваем логгер
        self.logger = logging.getLogger("openai_requests")
        self.logger.setLevel(logging.INFO)
        
        # Проверяем, есть ли уже обработчики
        if not self.logger.handlers:
            # Создаем файловый обработчик
            log_file = self.logs_dir / f"openai_requests_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Создаем форматтер
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Добавляем обработчик к логгеру
            self.logger.addHandler(file_handler)

    def log_request(self, user_id: int, messages):
        log_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        self.logger.info(json.dumps(log_data, ensure_ascii=False)) 