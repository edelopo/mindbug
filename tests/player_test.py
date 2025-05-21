import sys
import os

# Add the main project directory to the Python path
# Since we're in src/tests, we need to go one level up to access src/utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.player import Player
from src.utils.data_loader import load_cards_from_json
import traceback

def run_player_test():
    """
    Test the Player class by creating a player instance,
    drawing cards, discarding a card, and checking life points.
    """
    print("--- Starting Player Class Test ---")
    try:
        # Create a player instance
        player = Player(id="f13b3e")
        print(f"Created player: {player.id}")
        
        # Test initial state
        print(f"Initial life points: {player.life_points}")
        print(f"Initial mindbugs: {player.mindbugs}")
        print(f"Initial hand size: {len(player.hand)}")
        print(f"Initial deck size: {len(player.deck)}")

        # Test adding cards to deck
        # Since we're running from src/tests, we need to go up one level to reach the project root
        print("\n--- Testing create_deck method ---")
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_script_dir)  # Go up to the project root
        json_filepath = os.path.join(project_root, 'data', 'cards.json')

        cards = load_cards_from_json(json_filepath)
        player.deck = cards
        
        print(f"Deck size after adding cards: {len(player.deck)}")
        assert len(player.deck) == len(cards), "Deck size should match number of added cards"
        
        # Test drawing cards
        print("\n--- Testing draw_card method ---")
        initial_hand_size = len(player.hand)
        card = player.draw_card()
        print(f"Drew card: {card}")
        print(f"Hand size after drawing: {len(player.hand)}")
        assert len(player.hand) == initial_hand_size + 1, "Hand size should increase after drawing"
        
        # Draw multiple cards
        print("\n--- Testing draw_cards method ---")
        cards_to_draw = 3
        initial_hand_size = len(player.hand)
        drawn_cards = player.draw_card(cards_to_draw)
        print(f"Drew {len(drawn_cards)} cards")
        assert len(player.hand) == initial_hand_size + cards_to_draw, f"Hand should have {cards_to_draw} more cards"

        print(f"Hand after drawing: {player.hand}")
        
        # Test discarding a card
        print("\n--- Testing discard_card method ---")
        if player.hand:
            card_to_discard = player.hand[-1]
            print(f"Discarding card: {card_to_discard}")
            player.discard_card(card_to_discard)
            print(f"Hand size after discarding: {len(player.hand)}")
            assert card_to_discard not in player.hand, "Discarded card should not be in hand"
        
        # Test losing life points
        print("\n--- Testing lose_life method ---")
        initial_life = player.life_points
        life_to_lose = 2
        player.lose_life(life_to_lose)
        print(f"Life points after losing {life_to_lose}: {player.life_points}")
        assert player.life_points == initial_life - life_to_lose, f"Life should be {initial_life - life_to_lose}"
        
        # Test gaining life points
        print("\n--- Testing gain_life method ---")
        initial_life = player.life_points
        life_to_gain = 1
        player.gain_life(life_to_gain)
        print(f"Life points after gaining {life_to_gain}: {player.life_points}")
        assert player.life_points == initial_life + life_to_gain, f"Life should be {initial_life + life_to_gain}"
        
        print("\n--- Player class test PASSED! ---")
        
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")
        traceback.print_exc()
        sys.exit(1)  # Exit with an error code

if __name__ == "__main__":
    run_player_test()