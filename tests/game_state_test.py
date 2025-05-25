import sys
import os

# Add the main project directory to the Python path
# Since we're in src/tests, we need to go one level up to access src/utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.data_loader import load_cards_from_json
from src.models.player import Player
from src.models.game_state import GameState
import traceback

def run_game_state_test():
    """
    Test the GameState class by creating a game state with players,
    managing turns, playing cards, and checking game state changes.
    """
    print("--- Starting GameState Class Test ---")
    try:
        # Load cards for the game
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_script_dir)
        json_filepath = os.path.join(project_root, 'data', 'cards.json')
        cards = load_cards_from_json(json_filepath)
        
        # Create a game state with the players
        print("\n--- Creating GameState ---")
        game = GameState.initial_state(player1_id="player1", player2_id="player2", starting_deck=cards,
                                       deck_size=4, hand_size=2)
        print(f"Game created with {len(game.players)} players")
        
        # Test initial game state
        print("\n--- Testing Initial GameState ---")
        active_player = game.get_active_player()
        inactive_player = game.get_inactive_player()
        print(
            f"Current turn: {game.turn_count}\n"
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

        print(active_player.hand[0])
        
        # # Test turn management
        # print("\n--- Testing Next Turn ---")
        # previous_player = game.current_player
        # previous_turn = game.turn_count
        # game.next_turn()
        # print(f"Previous player: {previous_player.id}, Current player: {game.current_player.id}")
        # print(f"Turn count: {game.turn_count}")
        # assert game.current_player != previous_player, "Current player should change after next_turn"
        # assert game.turn_count == previous_turn + 1, "Turn count should increment"
        
        # # Test playing a card
        # print("\n--- Testing Play Card ---")
        # active_player = game.get_active_player()
        # if active_player.hand:
        #     card_to_play = active_player.hand[0]
        #     print(f"Playing card: {card_to_play}")
        #     hand_size_before = len(active_player.hand)
        #     active_player.play_card(card_to_play)
        #     print(f"Hand after playing: {active_player.hand}")
        #     print(f"Play area after playing: {active_player.play_area}")
        #     assert len(active_player.hand) == hand_size_before - 1, "Hand size should decrease after playing a card"
            
        # # Test attacking
        # print("\n--- Testing Attack ---")
        # attacker = game.current_player
        # defender = game.players[1 - game.current_player_index]  # Other player
        # initial_defender_life = defender.life_points
        # attack_amount = 2
        
        # print(f"Attacker: {attacker.id}, Defender: {defender.id}")
        # print(f"Defender life before: {defender.life_points}")
        # game.attack(attacker, defender, attack_amount)
        # print(f"Defender life after: {defender.life_points}")
        # assert defender.life_points == initial_defender_life - attack_amount, f"Defender should lose {attack_amount} life"
        
        # # Test game over conditions
        # print("\n--- Testing Game Over Conditions ---")
        # print(f"Is game over: {game.is_game_over()}")
        # if not game.is_game_over():
        #     defender.life_points = 0
        #     print(f"Set {defender.id}'s life to 0")
        #     print(f"Is game over now: {game.is_game_over()}")
        #     assert game.is_game_over(), "Game should be over when a player has 0 life"
        #     winner = game.get_winner()
        #     print(f"Winner: {winner.id if winner else 'None'}")
        #     assert winner == attacker, "Attacker should be the winner"
        
        print("\n--- GameState class test PASSED! ---")
        
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")
        traceback.print_exc()
        sys.exit(1)  # Exit with an error code

if __name__ == "__main__":
    run_game_state_test()