class Card:
    def __init__(self, card_id=None, name=None, power=None, keywords=None, ability_type=None, ability_text=None):
        """
        Initialize a Card object with data from cards.json
        
        Args:
            card_id (str): Unique identifier for the card
            name (str): Name of the card
            card_type (str): Type of the card (e.g., creature, spell)
            power (int, optional): Power value for creatures
            cost (int): Resource cost to play the card
            keywords (list): List of card keywords (e.g., poisonous, tough)
            ability_type (str): Type of ability (e.g., attack, passive)
            ability_text (str): Text description of the card
        """
        self.id = card_id
        self.name = name
        self.power = power
        self.keywords = keywords
        self.ability_type = ability_type
        self.ability_text = ability_text
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Card instance from a dictionary (typically from JSON)
        
        Args:
            data (dict): Dictionary containing card data
            
        Returns:
            Card: A new Card instance
        """
        return cls(
            card_id=data.get('id'),
            name=data.get('name'),
            power=data.get('power'),
            keywords=data.get('keywords'),
            ability_type=data.get('ability_type'),
            ability_text=data.get('ability_text')
        )
    
    def __repr__(self):
        """
        String representation of the Card for easy printing
        
        Returns:
            str: A formatted string with card information
        """
        return f"Card(ID: {self.id}, Name: '{self.name}', Power: {self.power}, Keywords: {self.keywords}, Abilities: {self.ability_text})"