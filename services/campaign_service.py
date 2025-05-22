from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class CampaignSettings:
    theme: str = ""
    world: str = ""
    characters: List[str] = field(default_factory=list)
    game_structure: str = ""
    additional_elements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class CampaignService:
    def __init__(self):
        self.campaigns: Dict[int, CampaignSettings] = {}

    def get_campaign(self, user_id: int) -> CampaignSettings:
        if user_id not in self.campaigns:
            self.campaigns[user_id] = CampaignSettings()
        return self.campaigns[user_id]

    def update_campaign(self, user_id: int, **kwargs) -> CampaignSettings:
        campaign = self.get_campaign(user_id)
        for key, value in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        campaign.updated_at = datetime.now()
        return campaign

    def get_formatted_settings(self, user_id: int) -> str:
        campaign = self.get_campaign(user_id)
        if not any([campaign.theme, campaign.world, campaign.characters, 
                   campaign.game_structure, campaign.additional_elements]):
            return "Настройки кампании не заданы. Используйте /campaign для настройки."

        formatted = "🎲 Настройки вашей кампании:\n\n"
        
        if campaign.theme:
            formatted += f"🎭 Тематика: {campaign.theme}\n"
        if campaign.world:
            formatted += f"🌍 Мир: {campaign.world}\n"
        if campaign.characters:
            formatted += f"👥 Персонажи:\n" + "\n".join(f"• {char}" for char in campaign.characters) + "\n"
        if campaign.game_structure:
            formatted += f"⏰ Структура игры: {campaign.game_structure}\n"
        if campaign.additional_elements:
            formatted += f"✨ Дополнительные элементы:\n" + "\n".join(f"• {elem}" for elem in campaign.additional_elements)
        
        return formatted 