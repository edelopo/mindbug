from typing import Set, Dict, Optional, Any

class Card:
    def __init__(self, card_id: Optional[str] = None, name: Optional[str] = None, 
                 power: Optional[int] = None, keywords: Optional[Set[str]] = None,
                 ability_type: Optional[str] = None, ability_text: Optional[str] = None) -> None:
        """
        Initialize a Card object with data from cards.json
        
        Args:
            card_id (str): Unique identifier for the card
            name (str): Name of the card
            power (int): Power value for creatures
            keywords (list): List of card keywords (e.g., poisonous, tough)
            ability_type (str): Type of ability (e.g., attack, passive)
            ability_text (str): Text description of the card
        """
        self.id: Optional[str] = card_id
        self.name: Optional[str] = name
        self.power: Optional[int] = power
        self.keywords: Set[str] = keywords or set()
        self.ability_type: Optional[str] = ability_type
        self.ability_text: Optional[str] = ability_text
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        """
        Create a Card instance from a dictionary (typically from JSON)
        
        Args:
            data (dict): Dictionary containing card data
            
        Returns:
            Card: A new Card instance
        """
        return cls(
            card_id = data.get('id'),
            name = data.get('name'),
            power = data.get('power'),
            keywords = set(data.get('keywords', [])),
            ability_type = data.get('ability_type'),
            ability_text = data.get('ability_text')
        )
    
    def __repr__(self) -> str:
        """
        String representation of the Card for easy printing
        
        Returns:
            str: A formatted string with card information
        """
        return f"Card(ID: {self.id}, Name: '{self.name}', Power: {self.power}, Keywords: {self.keywords}, Abilities: {self.ability_text})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
