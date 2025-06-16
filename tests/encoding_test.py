import sys
import os

# Add the main project directory to the Python path
# Since we're in src/tests, we need to go one level up to access src/utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.data_loader import load_definitions_from_json, load_cards_from_json
from src.models.player import Player
from src.models.game_state import GameState
from src.core.game_engine import GameEngine
from src.models.action import *
from src.utils.encoding import encode_game_state
import traceback
import json

def run_encoding_test():
    """
    Test the encoding by creating a game state and encoding it into a feature vector.
    This test will create a game state with two players, simulate some actions,
    and then encode the game state into a feature vector.
    """
    print("--- Starting Encoding Test ---")
    try:
        # Load cards and definitions for the game
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_script_dir)
        cards_json_filepath = os.path.join(project_root, 'data', 'cards.json')
        cards = load_cards_from_json(cards_json_filepath)

        deck_size = 10
        hand_size = 5

        # Create a game state with the players
        print("\n--- Creating GameState ---")
        game = GameState.initial_state(
            player1_id="player1", 
            player2_id="player2", 
            all_cards=cards,
            deck_size=deck_size,
            hand_size=hand_size)
        print(f"Game created with {len(game.players)} players")

        # Simulate some actions
        print("\n--- Simulating Actions ---")
        active_player = game.get_active_player()
        inactive_player = game.get_inactive_player()

        game_engine = GameEngine()

        # Example action: Player 1 plays a card from their hand
        if active_player.hand:
            card_to_play = active_player.hand[0]
            play_action = PlayCardAction(player_id=active_player.id, card_uuid=card_to_play.uuid)
            game = game_engine.apply_action(game, play_action)

        # Encode the game state
        print("\n--- Encoding Game State ---")
        feature_vector = encode_game_state(game)
        
        print("Feature vector:", feature_vector)
        print(f"Feature vector length: {len(feature_vector)}")

    except Exception as e:
        print("An error occurred during the encoding test:")
        traceback.print_exc()


if __name__ == "__main__":
    run_encoding_test()