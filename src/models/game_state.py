import random
from uuid import UUID
from typing import Dict, List, Optional, TYPE_CHECKING # For type hints
from src.models.player import Player
from src.models.card import Card

class GameState:
    def __init__(self,
                 active_player_id: str,
                 inactive_player_id: str,
                 players: Dict[str, Player],
                 turn_count: int,
                 phase: str,
                 game_over: bool = False,
                 winner_id: Optional[str] = None):
        """
        Initializes a new GameState object.

        Args:
            active_player_id: The ID of the player whose turn it currently is.
            inactive_player_id: The ID of the other player.
            players: A dictionary mapping player IDs to Player objects.
            turn_count: The current turn number.
            phase: The current phase of the turn (e.g., "mindbug_phase", "play_phase", etc.).
            game_over: Boolean indicating if the game has ended.
            winner_id: The ID of the winning player, if game_over is True.
        """
        self.active_player_id = active_player_id
        self.inactive_player_id = inactive_player_id
        self.players = players
        self.turn_count = turn_count
        self.phase = phase
        self.game_over = game_over
        self.winner_id = winner_id
        self._pending_mindbug_card_uuid: Optional[UUID] = None
        self._pending_attack_card_uuid: Optional[UUID] = None
        self._frenzy_active: bool = False

    @classmethod
    def initial_state(cls,
                      player1_id: str,
                      player2_id: str,
                      starting_deck: List[Card], # All starting cards from data/cards.json
                      deck_size: int = 10, # Standard deck size
                      hand_size: int = 5,
                      forced_cards_1: List[Card] = [],
                      forced_cards_2: List[Card] = []
                      ): # Standard hand size
        """
        Sets up the initial state for a new Mindbug game.

        Args:
            player1_id: The ID for the first player.
            player2_id: The ID for the second player.
            starting_deck: A list of all Cards, loaded from cards.json (e.g., via data_loader).
            deck_size: The number of creature cards each player starts with in their deck.
            hand_size: The number of cards each player draws at the start.

        Returns:
            A new GameState object representing the beginning of the game.
        """
        # Create a list of cards that are not in forced_cards
        other_cards = [card for card in starting_deck if (card not in forced_cards_1 and card not in forced_cards_2)]

        # Shuffle the common deck of cards
        random.shuffle(other_cards)

        # Distribute creature cards to decks
        if len(starting_deck) < deck_size * 2:
            raise ValueError(f"Not enough creature cards to form decks. Need at least {deck_size * 2}, but found {len(starting_deck)}.")

        player1_deck_list = forced_cards_1 + other_cards[0:deck_size-len(forced_cards_1)]
        player2_deck_list = forced_cards_2 + other_cards[deck_size-len(forced_cards_1):2*deck_size-len(forced_cards_2)]

        # Create Player objects
        player1 = Player(
            id=player1_id,
            deck=player1_deck_list
        )
        player2 = Player(
            id=player2_id,
            deck=player2_deck_list
        )

        players = {player1_id: player1, player2_id: player2}

        # Initial draw for both players
        for _ in range(hand_size):
            player1.draw_card()
            player2.draw_card()

        # Determine starting player (e.g., random or always P1)
        # For simplicity, let's say Player 1 starts
        active_player_id = player1_id
        inactive_player_id = player2_id

        return cls(
            active_player_id=active_player_id,
            inactive_player_id=inactive_player_id,
            players=players,
            turn_count=1, # Game starts at turn 1
            phase="play_phase",
            game_over=False,
            winner_id=None
        )

    def get_player(self, player_id: str) -> Player:
        """Helper to get a Player object by ID."""
        if player_id not in self.players:
            raise ValueError(f"Player with ID '{player_id}' not found in GameState.")
        return self.players[player_id]

    def get_active_player(self) -> Player:
        """Helper to get the currently active Player object."""
        return self.get_player(self.active_player_id)

    def get_inactive_player(self) -> Player:
        """Helper to get the currently inactive Player object."""
        return self.get_player(self.inactive_player_id)
    
    def get_opponent_of(self, player_id: str) -> Player:
        """
        Returns the opponent Player object for a given player ID.
        
        Args:
            player_id: The ID of the player whose opponent is requested.
        
        Returns:
            The Player object of the opponent.
        """
        if player_id == self.active_player_id:
            return self.get_inactive_player()
        elif player_id == self.inactive_player_id:
            return self.get_active_player()
        else:
            raise ValueError(f"Player with ID '{player_id}' is not part of this game.")

    def switch_active_player(self):
        """Switches the active and inactive players."""
        self.active_player_id, self.inactive_player_id = self.inactive_player_id, self.active_player_id

    def is_game_over(self) -> bool:
        """Checks if the game has ended."""
        # Mindbug win conditions:
        # 1. Opponent has no cards left in their life (unused) pile.
        # 2. Opponent has no creatures on battlefield and no cards in hand/deck.
        # This will be more complex and usually handled by the game engine,
        # but the GameState can expose the underlying data.
        return self.game_over

    def __repr__(self):
        active_player = self.get_active_player()
        inactive_player = self.get_inactive_player()

        return (
            f"--- GameState (Turn {self.turn_count}, Phase: {self.phase}) ---\n"
            f"Active Player: {active_player.id} (Life: {active_player.life_points}, Hand: {len(active_player.hand)}, Deck: {len(active_player.deck)}, Mindbugs: {active_player.mindbugs})\n"
            f"  Play area: {[c.name for c in active_player.play_area]}\n"
            f"Inactive Player: {inactive_player.id} (Life: {inactive_player.life_points}, Hand: {len(inactive_player.hand)}, Deck: {len(inactive_player.deck)}, Mindbugs: {inactive_player.mindbugs})\n"
            f"  Play area: {[c.name for c in inactive_player.play_area]}\n"
            f"Game Over: {self.game_over}, Winner: {self.winner_id if self.game_over else 'N/A'}"
        )