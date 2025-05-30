from typing import List, Optional
from src.models.card import Card
import copy

class Player:
    def __init__(self, id: str, deck: Optional[List[Card]] = None, hand: Optional[List[Card]] = None, 
                 discard_pile: Optional[List[Card]] = None, play_area: Optional[List[Card]] = None,
                 life_points: int = 3, mindbugs: int = 2) -> None:
        """
        Initialize a new player.
        
        Args:
            id: The player's id
            starting_life: Initial life points
            starting_mindbugs: Initial number of mindbugs
        """
        self.id: str = id
        self.deck: List[Card] = deck if deck is not None else []
        for card in self.deck:
            card.controller = self
        self.hand: List[Card] = hand if hand is not None else []
        for card in self.hand:
            card.controller = self
        self.discard_pile: List[Card] = discard_pile if discard_pile is not None else []
        for card in self.discard_pile:
            card.controller = self
        self.play_area: List[Card] = play_area if play_area is not None else []
        for card in self.play_area:
            card.controller = self
        self.life_points: int = life_points
        self.mindbugs: int = mindbugs
    
    def draw_card(self) -> Card:
        """
        Draw card from the top of the deck.
            
        Returns:
            List: Cards that were drawn
        """
        if self.deck:
            card = self.deck.pop(0)  # Take from the top of the deck
            self.hand.append(card)
        else:
            raise ValueError("No cards left in the deck to draw.")
        return card
    
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
            self.draw_card()
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
        if self.mindbugs > 0:
            self.mindbugs -= 1
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
        return f"Player {self.id}: {len(self.hand)} cards in hand, {self.life_points} life, {self.mindbugs} mindbugs"
    
    # def __deepcopy__(self) -> 'Player':
    #     """
    #     Create a deep copy of the player.
        
    #     Returns:
    #         Player: A new Player object with the same attributes
    #     """
    #     return Player(
    #         id=self.id,
    #         deck=copy.deepcopy(self.deck),
    #         hand=copy.deepcopy(self.hand),
    #         discard_pile=copy.deepcopy(self.discard_pile),
    #         play_area=copy.deepcopy(self.play_area),
    #         life_points=self.life_points,
    #         mindbugs=self.mindbugs
    #     )