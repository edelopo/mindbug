from typing import List, Dict, Any, Optional
from src.models.player import Player

class Card:
    def __init__(self, card_id: str, name: str, 
                 power: int, keywords: List[str],
                 ability_type: str, ability_text: str,
                 is_exhausted: bool = False, controller: Optional[Player] = None) -> None:
        """
        Initialize a Card object with data from cards.json
        
        Args:
            card_id: Unique identifier for the card
            name: Name of the card
            power: Power value for creatures
            keywords: List of card keywords (e.g., poisonous, tough)
            ability_type: Type of ability (e.g., attack, passive)
            ability_text: Text description of the card
        """
        self.id: str = card_id
        self.name: str = name
        self.power: int = power
        self.keywords: List[str] = keywords or []
        self.ability_type: str = ability_type
        self.ability_text: str = ability_text
        self.is_exhausted: bool = is_exhausted
        self.controller: Optional[Player] = controller
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        """
        Create a Card instance from a dictionary (typically from JSON)
        
        Args:
            data: Dictionary containing card data
            
        Returns:
            Card: A new Card instance
        """
        return cls(
            card_id = data.get('id', ''),
            name = data.get('name', ''),
            power = data.get('power', -1),
            keywords = data.get('keywords', []),
            ability_type = data.get('ability_type', ''),
            ability_text = data.get('ability_text', '')
        )
    
    def __repr__(self) -> str:
        """
        String representation of the Card for easy printing
        
        Returns:
            str: A formatted string with card information
        """
        return f"Card(ID: {self.id}, Name: '{self.name}', Power: {self.power}, Keywords: {self.keywords}, Abilities: {self.ability_text})"