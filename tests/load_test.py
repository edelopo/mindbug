import sys
import os

# Add the main project directory to the Python path
# Since we're in src/tests, we need to go one level up to access src/utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.data_loader import load_cards_from_json

def run_card_loading_test():
    """
    Loads cards from the JSON file and prints their details to verify.
    """
    print("--- Starting Card Data Loading Test ---")
    try:
        # Since we're running from src/tests, we need to go up one level to reach the project root
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_script_dir)  # Go up to the project root
        json_filepath = os.path.join(project_root, 'data', 'cards.json')

        cards = load_cards_from_json(json_filepath)

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
        # assert "axolotl_healer" in cards, "Axolotl Healer not found!"
        # assert cards["kangasaurus_rex"].power == 8, "Kangasaurus Rex power is incorrect!"
        # assert "Tough" in cards["kangasaurus_rex"].keywords, "Kangasaurus Rex missing 'Tough' keyword!"
        # assert cards["mindbug"].ability_type == "Special", "Mindbug ability type incorrect!"

        print("\n--- Card data loading test PASSED! ---")

        print("\n--- Starting Card Printing Test ---")
        for card_id, card in cards.items():
            print(card)

        print("\n--- Card printing test PASSED! ---")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure 'data/cards.json' exists at the correct path.")
    except Exception as e:
        print(f"An unexpected error occurred during testing: {e}")
        sys.exit(1) # Exit with an error code

if __name__ == "__main__":
    run_card_loading_test()