class Player:
    def __init__(self, name, starting_life=3, starting_mindbugs=2):
        """
        Initialize a new player.
        
        Args:
            name (str): The player's name
            starting_life (int): Initial life points
            starting_mindbugs (int): Initial number of mindbugs
        """
        self.name = name
        self.hand = []
        self.deck = []
        self.discard_pile = []
        self.play_area = []
        self.life_points = starting_life
        self.mindbugs_remaining = starting_mindbugs
    
    def draw_card(self, count=1):
        """
        Draw cards from the top of the deck.
        
        Args:
            count (int): Number of cards to draw
            
        Returns:
            list: Cards that were drawn
        """
        drawn_cards = []
        for _ in range(min(count, len(self.deck))):
            if self.deck:
                card = self.deck.pop(0)  # Take from the top of the deck
                self.hand.append(card)
                drawn_cards.append(card)
        return drawn_cards
    
    def discard_card(self, card):
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
    
    def add_to_hand(self, card):
        """
        Add a card to the player's hand.
        
        Args:
            card: The card to add
        """
        self.hand.append(card)
    
    def lose_life(self, amount=1):
        """
        Player loses life points.
        
        Args:
            amount (int): Amount of life to lose
            
        Returns:
            int: Current life points after loss
        """
        self.life_points = max(0, self.life_points - amount)
        return self.life_points
    
    def gain_life(self, amount=1):
        """
        Player gains life points.
        
        Args:
            amount (int): Amount of life to gain
            
        Returns:
            int: Current life points after gain
        """
        self.life_points += amount
        return self.life_points
    
    def use_mindbug(self):
        """
        Use a mindbug ability.
        
        Returns:
            bool: True if a mindbug was used, False if none remaining
        """
        if self.mindbugs_remaining > 0:
            self.mindbugs_remaining -= 1
            return True
        return False
    
    def play_card(self, card):
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
    
    def __str__(self):
        return f"Player {self.name}: {len(self.hand)} cards in hand, {self.life_points} life, {self.mindbugs_remaining} mindbugs"