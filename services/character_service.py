import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

class CharacterService:
    def __init__(self, characters_base_path: str = "../character_manage_bot/characters"):
        self.characters_base_path = Path(characters_base_path)

    def get_active_character(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the active character for a specific user
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            Optional[Dict[str, Any]]: Active character data or None if not found
        """
        user_dir = self.characters_base_path / str(user_id)
        
        if not user_dir.exists():
            return None
            
        # Iterate through all JSON files in user's directory
        for char_file in user_dir.glob("*.json"):
            try:
                with open(char_file, 'r', encoding='utf-8') as f:
                    character_data = json.load(f)
                    if character_data.get('is_active', False):
                        return character_data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading character file {char_file}: {e}")
                continue
                
        return None

    def set_active_character(self, user_id: int, character_name: str) -> bool:
        """
        Set a specific character as active for a user
        
        Args:
            user_id (int): Telegram user ID
            character_name (str): Name of the character to set as active
            
        Returns:
            bool: True if successful, False otherwise
        """
        user_dir = self.characters_base_path / str(user_id)
        
        if not user_dir.exists():
            return False
            
        success = False
        target_file = None
        
        # First, deactivate all characters
        for char_file in user_dir.glob("*.json"):
            try:
                with open(char_file, 'r+', encoding='utf-8') as f:
                    character_data = json.load(f)
                    if character_data.get('name') == character_name:
                        target_file = char_file
                    character_data['is_active'] = False
                    f.seek(0)
                    json.dump(character_data, f, ensure_ascii=False, indent=2)
                    f.truncate()
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error updating character file {char_file}: {e}")
                continue
                
        # Then activate the target character
        if target_file:
            try:
                with open(target_file, 'r+', encoding='utf-8') as f:
                    character_data = json.load(f)
                    character_data['is_active'] = True
                    f.seek(0)
                    json.dump(character_data, f, ensure_ascii=False, indent=2)
                    f.truncate()
                    success = True
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error activating character file {target_file}: {e}")
                
        return success 