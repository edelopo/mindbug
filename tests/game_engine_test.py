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
import traceback

def run_game_engine_test():
    """
    Test the GameEngine class by creating a game state with players,
    managing turns, playing cards, and checking game state changes.
    """
    print("--- Starting GameEngine Class Test ---")
    try:
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
        
        # Test initial game state
        print("\n--- Testing Initial GameState ---")
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()
        print(
            f"Current turn: {game_state.turn_count}\n"
            f"Active player: {active_player.id}\n"
            f"  Hand size: {len(active_player.hand)}\n"
            f"  Hand: {[card.name for card in active_player.hand]}\n"
            f"  Deck size: {len(active_player.deck)}\n"
            f"  Deck: {[card.name for card in active_player.deck]}\n"
            f"  Play area: {active_player.play_area}\n"
            f"Inactive player: {inactive_player.id}\n"
            f"  Hand size: {len(inactive_player.hand)}\n"
            f"  Hand: {[card.name for card in inactive_player.hand]}\n"
            f"  Deck size: {len(inactive_player.deck)}\n"
            f"  Deck: {[card.name for card in inactive_player.deck]}\n"
            f"  Play area: {inactive_player.play_area}\n"
        )
        
        # # Test turn management
        # print("\n--- Testing Next Turn ---")
        # print(f"Turn count before: {game_state.turn_count}, Active player before: {game_state.active_player_id}")
        # game_engine.end_turn(game_state)
        
        # Test playing a card and passing Mindbug
        print("\n--- Testing Play Card ---")
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()
        if player.hand:
            card_to_play = player.hand[0]
            game_state = game_engine.apply_action(game_state, PlayCardAction(player.id, card_to_play.uuid))
            # Now that the game state has been updated, we can no longer use player and opponent: they are outdated
            game_state = game_engine.apply_action(game_state, PassMindbugAction(game_state.get_active_player().id))
        else:
            raise ValueError("Active player has no cards to play, but they should.")
        
        # Test playing a card and using Mindbug
        print("\n--- Testing Use Mindbug ---")
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()
        if player.hand:
            card_to_play = player.hand[0]
            game_state = game_engine.apply_action(game_state, PlayCardAction(player.id, card_to_play.uuid))
            # Now that the game state has been updated, we need to get the player and opponent again
            game_state = game_engine.apply_action(game_state, UseMindbugAction(game_state.get_active_player().id))
        else:
            raise ValueError("Active player has no cards to play, but they should.")
            
        # Test attacking
        print("\n--- Testing Attack ---")
        game_state = game_engine.end_turn(game_state)  # Pass turn so that the attacker has cards in play
        attacker = game_state.get_active_player()
        defender = game_state.get_inactive_player()
        initial_defender_life = defender.life_points
        
        # Assuming the played card is a creature that can attack
        if attacker.play_area:
            attacking_card = attacker.play_area[0]
            
            game_state = game_engine.apply_action(game_state, AttackAction(attacker.id, attacking_card.uuid))
            defender = game_state.get_active_player()  # Get updated defender after attack (active player has changed)
            assert defender.life_points < initial_defender_life, "Defender should lose life after attack"

        # Test blocking an attack
        print("\n--- Testing Block ---")

        
        # # Test game over conditions
        # print("\n--- Testing Game Over Conditions ---")
        # is_game_over = game_engine.check_game_over(game_state)
        # print(f"Is game over: {is_game_over}")
        # if not is_game_over:
        #     defender.life_points = 0
        #     print(f"Set {defender.id}'s life to 0")
        #     is_game_over = game_engine.check_game_over(game_state)
        #     print(f"Is game over now: {is_game_over}")
        #     assert is_game_over, "Game should be over when a player has 0 life"
        #     winner = game_engine.get_winner(game_state)
        #     print(f"Winner: {winner}")
        #     assert winner == attacker.id, "Attacker should be the winner"
        
        print("\n--- GameEngine class test PASSED! ---")
        
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")
        traceback.print_exc()
        sys.exit(1)  # Exit with an error code

if __name__ == "__main__":
    run_game_engine_test()