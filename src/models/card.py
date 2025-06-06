from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
import copy
if TYPE_CHECKING:
    from src.models.player import Player

class Card:
    def __init__(self, id:str, name: str, 
                 power: int, keywords: List[str],
                 ability_type: str, ability_text: str,
                 is_exhausted: bool = False, controller: Optional['Player'] = None) -> None:
        """
        Initialize a Card object with data from cards.json
        
        Args:
            uuid: Code-appropiate identifier for the card
            name: Name of the card
            power: Power value for creatures
            keywords: List of card keywords (e.g., poisonous, tough)
            ability_type: Type of ability (e.g., attack, passive)
            ability_text: Text description of the card
        """
        self.uuid: UUID = uuid4()  # Generate a unique ID for the card
        self.id: str = id
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
            id = data.get('id', ''),
            name = data.get('name', ''),
            power = data.get('base_power', -1),
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
        return f"Card(ID: {self.id}, UUID: {self.uuid}, Controller: {self.controller.id if self.controller else 'None'}"
    
    def __str__(self) -> str:
        """
        String representation of the Card for easy printing
        
        Returns:
            str: A formatted string with card information
        """
        text = (
            f"Card Details:\n"
            f"----------------\n"
            f"| Name: {self.name}\n" 
            f"| ID: {self.id}\n"
            f"| UUID: {self.uuid}\n"
            f"| Power: {self.power}\n"
            f"| Keywords: {', '.join(self.keywords) if self.keywords else 'None'}\n"
            f"| Abilities: {self.ability_text if self.ability_text else 'None'}"
        )
        return text
    
    # def __deepcopy__(self) -> 'Card':
    #     """
    #     Create a deep copy of the card.
    #     Returns:
    #         Card: A new Card object with the same attributes
    #     """
    #     return Card(
    #         card_id=self.id,
    #         name=self.name,
    #         power=self.power,
    #         keywords=copy.deepcopy(self.keywords),
    #         ability_type=self.ability_type,
    #         ability_text=self.ability_text,
    #         is_exhausted=self.is_exhausted,
    #         controller=self.controller
    #     )