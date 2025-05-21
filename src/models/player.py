from typing import List
from src.models.card import Card

class Player:
    def __init__(self, name: str, starting_life: int = 3, starting_mindbugs: int = 2) -> None:
        """
        Initialize a new player.
        
        Args:
            name: The player's name
            starting_life: Initial life points
            starting_mindbugs: Initial number of mindbugs
        """
        self.name: str = name
        self.hand: List[Card] = []
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []
        self.play_area: List[Card] = []
        self.life_points: int = starting_life
        self.mindbugs_remaining: int = starting_mindbugs

    def create_deck(self, source_deck: List[Card], size: int = 10) -> None:
        """
        Create a deck of cards for the player.
        
        Args:
            source_deck: Source deck to draw from
            size: Number of cards to include in the deck
        """
        self.deck = source_deck[:size]
    
    def draw_card(self, count: int = 1) -> List[Card]:
        """
        Draw cards from the top of the deck.
        
        Args:
            count: Number of cards to draw
            
        Returns:
            List: Cards that were drawn
        """
        drawn_cards: List[Card] = []
        for _ in range(min(count, len(self.deck))):
            if self.deck:
                card = self.deck.pop(0)  # Take from the top of the deck
                self.hand.append(card)
                drawn_cards.append(card)
        return drawn_cards
    
    def discard_card(self, card: Card) -> bool:
        """
        Discard a card from hand to discard pile.
        
        Args:
            card: The card to discard
            
        Returns:
            bool: True if successful, False if card not in hand
        """
        if card in self.hand:
            self.hand.remove(card)
            self.discard_pile.append(card)
            return True
        return False
    
    def add_to_hand(self, card: Card) -> None:
        """
        Add a card to the player's hand.
        
        Args:
            card: The card to add
        """
        self.hand.append(card)
    
    def lose_life(self, amount: int = 1) -> int:
        """
        Player loses life points.
        
        Args:
            amount: Amount of life to lose
            
        Returns:
            int: Current life points after loss
        """
        self.life_points = max(0, self.life_points - amount)
        return self.life_points
    
    def gain_life(self, amount: int = 1) -> int:
        """
        Player gains life points.
        
        Args:
            amount: Amount of life to gain
            
        Returns:
            int: Current life points after gain
        """
        self.life_points += amount
        return self.life_points
    
    def use_mindbug(self) -> bool:
        """
        Use a mindbug ability.
        
        Returns:
            bool: True if a mindbug was used, False if none remaining
        """
        if self.mindbugs_remaining > 0:
            self.mindbugs_remaining -= 1
            return True
        return False
    
    def play_card(self, card: Card) -> bool:
        """
        Play a card from hand to play area.
        
        Args:
            card: The card to play
            
        Returns:
            bool: True if successful, False if card not in hand
        """
        if card in self.hand:
            self.hand.remove(card)
            self.play_area.append(card)
            return True
        return False
    
    def __str__(self) -> str:
        return f"Player {self.name}: {len(self.hand)} cards in hand, {self.life_points} life, {self.mindbugs_remaining} mindbugs"