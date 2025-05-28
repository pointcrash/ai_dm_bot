from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import json
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CampaignData:
    """Класс для хранения данных кампании"""
    description: str
    updated_at: datetime = datetime.now()

class CampaignService:
    """Сервис для управления описаниями кампаний"""
    
    def __init__(self, campaigns_dir: str = "data/campaigns") -> None:
        """
        Инициализация сервиса
        
        Args:
            campaigns_dir: Путь к директории для хранения описаний кампаний
        """
        self.campaigns_dir = Path(campaigns_dir)
        self._ensure_campaigns_dir()

    def _ensure_campaigns_dir(self) -> None:
        """Создает директорию для хранения описаний кампаний, если она не существует"""
        try:
            self.campaigns_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Ошибка при создании директории кампаний: {e}")
            raise

    def _get_campaign_file_path(self, chat_id: int) -> Path:
        """
        Возвращает путь к файлу описания кампании
        
        Args:
            chat_id: ID чата
            
        Returns:
            Path: Путь к файлу кампании
        """
        return self.campaigns_dir / f"campaign_{chat_id}.json"

    def get_campaign(self, chat_id: int) -> CampaignData:
        """
        Получить данные кампании для чата
        
        Args:
            chat_id: ID чата
            
        Returns:
            CampaignData: Данные кампании
        """
        campaign_file = self._get_campaign_file_path(chat_id)
        if not campaign_file.exists():
            return CampaignData(description="")
            
        try:
            with open(campaign_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CampaignData(
                    description=data.get('description', ''),
                    updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
                )
        except Exception as e:
            logger.error(f"Ошибка при чтении кампании {chat_id}: {e}")
            return CampaignData(description="")

    def update_campaign(self, chat_id: int, **kwargs) -> CampaignData:
        """
        Обновить данные кампании
        
        Args:
            chat_id: ID чата
            **kwargs: Параметры для обновления
            
        Returns:
            CampaignData: Обновленные данные кампании
        """
        campaign = self.get_campaign(chat_id)
        
        # Обновляем только разрешенные поля
        if 'description' in kwargs:
            campaign.description = kwargs['description']
        campaign.updated_at = datetime.now()
        
        # Сохраняем изменения
        try:
            data = {
                'description': campaign.description,
                'updated_at': campaign.updated_at.isoformat()
            }
            
            with open(self._get_campaign_file_path(chat_id), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении кампании {chat_id}: {e}")
            
        return campaign

    def delete_campaign(self, chat_id: int) -> bool:
        """
        Удалить описание кампании
        
        Args:
            chat_id: ID чата
            
        Returns:
            bool: True если удаление успешно, False в случае ошибки
        """
        try:
            campaign_file = self._get_campaign_file_path(chat_id)
            if campaign_file.exists():
                campaign_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении кампании {chat_id}: {e}")
            return False