import sys
import os

# Add the src directory to the Python path
# This allows you to import modules from src/ like src.utils.data_loader
# without issues when running from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.data_loader import load_cards_from_json

def run_card_loading_test():
    """
    Loads cards from the JSON file and prints their details to verify.
    """
    print("--- Starting Card Data Loading Test ---")
    try:
        # Assuming cards.json is in data/ relative to the project root
        # You might need to adjust the path if running from a different directory
        current_script_dir = os.path.dirname(__file__)
        json_filepath = os.path.join(current_script_dir, 'data', 'cards.json')

        cards = load_cards_from_json(filepath=json_filepath)

        print(f"\nSuccessfully loaded {len(cards)} cards.")
        print("\n--- Details of loaded cards: ---")
        for card_id, card in cards.items():
            print(f"- {card.name} (ID: {card.id})")
            print(f"  Power: {card.power}")
            print(f"  Keywords: {', '.join(card.keywords) if card.keywords else 'None'}")
            print(f"  Ability Type: {card.ability_type}")
            print(f"  Ability Text: {card.ability_text}")
            print("-" * 20)

        # Basic assertions for testing
        assert "axolotl_healer" in cards, "Axolotl Healer not found!"
        assert cards["kangasaurus_rex"].power == 8, "Kangasaurus Rex power is incorrect!"
        assert "Tough" in cards["kangasaurus_rex"].keywords, "Kangasaurus Rex missing 'Tough' keyword!"
        assert cards["mindbug"].ability_type == "Special", "Mindbug ability type incorrect!"

        print("\n--- Card data loading test PASSED! ---")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure 'data/cards.json' exists at the correct path.")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")
        sys.exit(1) # Exit with an error code

if __name__ == "__main__":
    run_card_loading_test()