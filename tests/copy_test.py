import sys
import os
import copy

# Add the main project directory to the Python path
# Since we're in src/tests, we need to go one level up to access src/utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.data_loader import load_definitions_from_json, load_cards_from_json
from src.models.player import Player
from src.models.game_state import GameState
from src.core.game_engine import GameEngine
from src.models.action import PlayCardAction, PassMindbugAction, UseMindbugAction

def run_test():
    """
    Test the GameEngine class by creating a game state with players,
    managing turns, playing cards, and checking game state changes.
    """
    print("--- Starting GameEngine Class Test ---")

    # Load cards for the game
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    json_filepath = os.path.join(project_root, 'data', 'cards.json')
    card_definitions = load_definitions_from_json(json_filepath)
    cards = load_cards_from_json(json_filepath)
    
    # Create a game engine with initial state
    print("\n--- Creating GameEngine ---")
    game_engine = GameEngine(card_definitions, deck_size=4, hand_size=2)
    game_state = GameState.initial_state(player1_id="player1", player2_id="player2", starting_deck=cards,
                                    deck_size=game_engine.game_rules.deck_size, 
                                    hand_size=game_engine.game_rules.hand_size)
    print(f"Game created with {len(game_state.players)} players")

    game_state.get_active_player().draw_card()

    new_state = copy.deepcopy(game_state)

    print(new_state)

if __name__ == "__main__":
    run_test()