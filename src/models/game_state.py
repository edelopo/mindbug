# # src/models/game_state.py
# import random
# from typing import Dict, List, Optional # For type hints
# from src.models.player import Player
# from src.models.card import Card

# class GameState:
#     def __init__(self,
#                  active_player_id: str,
#                  inactive_player_id: str,
#                  players: Dict[str, Player],
#                  turn_count: int,
#                  phase: str,
#                  game_over: bool = False,
#                  winner_id: Optional[str] = None):
#         """
#         Initializes a new GameState object.

#         Args:
#             active_player_id: The ID of the player whose turn it currently is.
#             inactive_player_id: The ID of the other player.
#             players: A dictionary mapping player IDs to Player objects.
#             turn_count: The current turn number.
#             phase: The current phase of the turn (e.g., "draw", "play", "resolve", "end").
#             game_over: Boolean indicating if the game has ended.
#             winner_id: The ID of the winning player, if game_over is True.
#         """
#         self.active_player_id = active_player_id
#         self.inactive_player_id = inactive_player_id
#         self.players = players
#         self.turn_count = turn_count
#         self.phase = phase
#         self.game_over = game_over
#         self.winner_id = winner_id

#     @classmethod
#     def initial_state(cls,
#                       player1_id: str,
#                       player2_id: str,
#                       all_available_cards: Dict[str, Card], # All cards from data/cards.json
#                       num_creatures_per_deck: int = 10, # Standard Mindbug deck size
#                       initial_hand_size: int = 5): # Standard Mindbug hand size
#         """
#         Sets up the initial state for a new Mindbug game.

#         Args:
#             player1_id: The ID for the first player.
#             player2_id: The ID for the second player.
#             all_available_cards: A dictionary of all possible Card objects,
#                                  loaded from cards.json (e.g., via data_loader).
#             num_creatures_per_deck: The number of creature cards each player starts with in their deck.
#             initial_hand_size: The number of cards each player draws at the start.

#         Returns:
#             A new GameState object representing the beginning of the game.
#         """

#         # Create the commond deck of cards
#         cards = []
#         for card_id, card in all_available_cards.items():
#             for _ in range(card.count):
#                 cards.append(card.copy())
#         random.shuffle(cards)

#         # Distribute creature cards to decks
#         if len(creature_cards) < num_creatures_per_deck * 2:
#             raise ValueError(f"Not enough creature cards to form decks. Need at least {num_creatures_per_deck * 2}, but found {len(creature_cards)}.")

#         player1_deck_list = creature_cards[0:num_creatures_per_deck]
#         player2_deck_list = creature_cards[num_creatures_per_deck:num_creatures_per_deck * 2]
        
#         # Remaining cards become the unused pile for life points
#         # In Mindbug, unused cards from the draw pile become life points.
#         # So we include all cards that were *not* used for decks in the unused pile.
#         unused_cards_list = creature_cards[num_creatures_per_deck * 2:]
        
#         # Add Mindbug cards to each player's specific Mindbug pile
#         player1_mindbugs = [mindbug_card, mindbug_card] # Each player starts with 2 Mindbugs
#         player2_mindbugs = [mindbug_card, mindbug_card]

#         # Create Player objects
#         player1 = Player(
#             player_id=player1_id,
#             deck=deque(player1_deck_list), # Use deque for efficient pop from start/end
#             mindbugs=deque(player1_mindbugs)
#         )
#         player2 = Player(
#             player_id=player2_id,
#             deck=deque(player2_deck_list),
#             mindbugs=deque(player2_mindbugs)
#         )

#         players = {player1_id: player1, player2_id: player2}

#         # Initial draw for both players
#         for _ in range(initial_hand_size):
#             player1.draw_card()
#             player2.draw_card()

#         # Determine starting player (e.g., random or always P1)
#         # For simplicity, let's say Player 1 starts
#         active_player_id = player1_id
#         inactive_player_id = player2_id

#         # Initialize battlefield, discard pile, and unused pile
#         battlefield = {player1_id: [], player2_id: []}
#         discard_pile = [] # Central discard pile
        
#         # In Mindbug, the unused cards from the deck generation are the "life points"
#         # represented by the unused pile.
#         life_unused_pile = unused_cards_list

#         return cls(
#             active_player_id=active_player_id,
#             inactive_player_id=inactive_player_id,
#             players=players,
#             turn_count=1, # Game starts at turn 1
#             phase="draw_phase", # Or "start_of_turn_phase"
#             battlefield=battlefield,
#             discard_pile=discard_pile,
#             unused_pile=life_unused_pile, # Use the remaining creature cards here
#             game_over=False,
#             winner_id=None
#         )

#     def get_player(self, player_id: str) -> Player:
#         """Helper to get a Player object by ID."""
#         if player_id not in self.players:
#             raise ValueError(f"Player with ID '{player_id}' not found in GameState.")
#         return self.players[player_id]

#     def get_active_player(self) -> Player:
#         """Helper to get the currently active Player object."""
#         return self.get_player(self.active_player_id)

#     def get_inactive_player(self) -> Player:
#         """Helper to get the currently inactive Player object."""
#         return self.get_player(self.inactive_player_id)

#     def switch_active_player(self):
#         """Switches the active and inactive players."""
#         self.active_player_id, self.inactive_player_id = self.inactive_player_id, self.active_player_id

#     def is_game_over(self) -> bool:
#         """Checks if the game has ended."""
#         # Mindbug win conditions:
#         # 1. Opponent has no cards left in their life (unused) pile.
#         # 2. Opponent has no creatures on battlefield and no cards in hand/deck.
#         # This will be more complex and usually handled by the game engine,
#         # but the GameState can expose the underlying data.
#         return self.game_over

#     # For AI, it's often useful to create a deep copy of the state
#     # before applying an action, especially if you're using a mutable state.
#     # If your GameEngine methods modify the state in place, you NEED this.
#     # If they return a *new* state, this isn't strictly necessary for every step,
#     # but still good for initial state exploration in AI.
#     def copy(self):
#         """
#         Creates a deep copy of the current GameState.
#         Crucial for AI algorithms like MCTS that need to simulate many futures
#         without altering the original state.
#         """
#         # Deep copy all mutable containers
#         players_copy = {
#             pid: player.copy() # Assuming Player has a copy method
#             for pid, player in self.players.items()
#         }
#         battlefield_copy = {
#             pid: [c.copy() for c in creatures] # Assuming Creature has a copy method
#             for pid, creatures in self.battlefield.items()
#         }
#         discard_pile_copy = [c.copy() for c in self.discard_pile] # Assuming Card has a copy method
#         unused_pile_copy = [c.copy() for c in self.unused_pile] # Assuming Card has a copy method

#         return GameState(
#             active_player_id=self.active_player_id,
#             inactive_player_id=self.inactive_player_id,
#             players=players_copy,
#             turn_count=self.turn_count,
#             phase=self.phase,
#             battlefield=battlefield_copy,
#             discard_pile=discard_pile_copy,
#             unused_pile=unused_pile_copy,
#             game_over=self.game_over,
#             winner_id=self.winner_id
#         )

#     def __repr__(self):
#         active_player = self.get_active_player()
#         inactive_player = self.get_inactive_player()

#         return (
#             f"--- GameState (Turn {self.turn_count}, Phase: {self.phase}) ---\n"
#             f"Active Player: {active_player.player_id} (Life: {len(active_player.unused_pile_for_life)}, Hand: {len(active_player.hand)}, Deck: {len(active_player.deck)}, Mindbugs: {len(active_player.mindbugs)})\n"
#             f"  Battlefield: {[c.name for c in self.battlefield[active_player.player_id]]}\n"
#             f"Inactive Player: {inactive_player.player_id} (Life: {len(inactive_player.unused_pile_for_life)}, Hand: {len(inactive_player.hand)}, Deck: {len(inactive_player.deck)}, Mindbugs: {len(inactive_player.mindbugs)})\n"
#             f"  Battlefield: {[c.name for c in self.battlefield[inactive_player.player_id]]}\n"
#             f"Central Discard: {len(self.discard_pile)} cards\n"
#             f"Central Unused: {len(self.unused_pile)} cards\n"
#             f"Game Over: {self.game_over}, Winner: {self.winner_id if self.game_over else 'N/A'}"
#         )