# CLI = Command Line Interface
from src.models.game_state import GameState
from src.models.action import Action, CardChoiceRequest
from src.models.card import Card
from typing import List, Dict
import src.core.game_rules as GameRules
import os

class MindbugCLI:
    def display_game_state(self, game_state: GameState):
        """
        Displays the current state of the game to the console with improved formatting.
        """
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()

        # os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for better readability

        # Game header with turn info
        print("\n" + "╔" + "═"*70 + "╗")
        print(f"║{'TURN ' + str(game_state.turn_count) + ' - PHASE: ' + game_state.phase.upper():^70}║")
        print("╚" + "═"*70 + "╝")

        # Active player indicator
        print(f"\n▶ {active_player.id}'s TURN")

        # Active player's board
        print(f"\n┌{'─'*68}┐")
        print(f"│ {active_player.id}'s Board{' '*(68 - len(active_player.id) - 9)}│")
        print(f"├{'─'*68}┤")
        print(f"│{' ':>4}Life: {active_player.life_points:2d}{' ':>3}│{' ':>3}Mindbugs: {active_player.mindbugs:2d}{' ':>3}│{' ':>3}Deck: {len(active_player.deck):2d}{' ':>3}│{' ':>3}Discard: {len(active_player.discard_pile):2d}{' ':>4}│")
        print(f"├{'─'*68}┤")
        
        # Hand display
        print(f"│ Hand ({len(active_player.hand)} cards):{' '*(68 - len(f'Hand ({len(active_player.hand)} cards):') - 1)}│")
        if active_player.hand:
            for i, card in enumerate(active_player.hand):
                card_str = f"│  {i+1}. {card.name:<25} (Power: {card.power})"
                print(f"{card_str}{' '*(69 - len(card_str))}│")
        else:
            print(f"│  (Empty){' '*59}│")
        
        # Play area display
        print(f"├{'─'*68}┤")
        print(f"│ Play Area ({len(active_player.play_area)} cards):{' '*(68 - len(f'Play Area ({len(active_player.play_area)} cards):') - 1)}│")
        if active_player.play_area:
            for i, card in enumerate(active_player.play_area):
                exhausted = "⚠ EXHAUSTED" if card.is_exhausted else ""
                eff_power = GameRules.get_effective_power(game_state, card.uuid)
                card_str = f"│  {i+1}. {card.name:<25} (Power: {eff_power:2d}) {exhausted}"
                print(f"{card_str}{' '*(69 - len(card_str))}│")
        else:
            print(f"│  (Empty){' '*59}│")
        print(f"└{'─'*68}┘")

        # Inactive player's board
        print(f"\n┌{'─'*68}┐")
        print(f"│ {inactive_player.id}'s Board{' '*(68 - len(inactive_player.id) - 9)}│")
        print(f"├{'─'*68}┤")
        print(f"│{' ':>4}Life: {inactive_player.life_points:2d}{' ':>3}│{' ':>3}Mindbugs: {inactive_player.mindbugs:2d}{' ':>3}│{' ':>3}Deck: {len(inactive_player.deck):2d}{' ':>3}│{' ':>3}Discard: {len(inactive_player.discard_pile):2d}{' ':>4}│")
        print(f"├{'─'*68}┤")
        print(f"│ Hand: {len(inactive_player.hand)} cards{' '*(68 - len(f'Hand: {len(inactive_player.hand)} cards') - 1)}│")
        
        # Play area display
        print(f"├{'─'*68}┤")
        print(f"│ Play Area ({len(inactive_player.play_area)} cards):{' '*(68 - len(f'Play Area ({len(inactive_player.play_area)} cards):') - 1)}│")
        if inactive_player.play_area:
            for i, card in enumerate(inactive_player.play_area):
                exhausted = "⚠ EXHAUSTED" if card.is_exhausted else ""
                eff_power = GameRules.get_effective_power(game_state, card.uuid)
                card_str = f"│  {i+1}. {card.name:<25} (Power: {eff_power:2d}) {exhausted}"
                print(f"{card_str}{' '*(69 - len(card_str))}│")
        else:
            print(f"│  (Empty){' '*59}│")
        print(f"└{'─'*68}┘\n")

    def get_player_action(self, possible_actions: List[Dict[str, Action | str]]) -> Action:
        """
        Prompts the human player to choose an action from a list of possibilities.
        """
        print("\nPossible actions:")
        for i, action in enumerate(possible_actions):
            if 'card_name' in action.keys():
                print(f"{i + 1}. {action['action']} - Card: {action['card_name']}")
            else:
                print(f"{i + 1}. {action['action']}")

        while True:
            try:
                choice = input("Enter the number of your chosen action: ")
                action_index = int(choice) - 1
                if 0 <= action_index < len(possible_actions):
                    action = possible_actions[action_index]['action']
                    if isinstance(action, Action):
                        return action
                    else:
                        raise ValueError("Invalid action type.")
                else:
                    print("❌ Invalid action number. Please try again.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")

    def get_card_choice(self, game_state: GameState, choice_request: CardChoiceRequest) -> List[Card]:
        """
        Prompts the player to select cards from the given options.
        """
        # Card selection header with decorative box
        print("\n" + "╔" + "═"*70 + "╗")
        print(f"║{'CARD SELECTION':^70}║")
        print("╚" + "═"*70 + "╝")
        
        # Display the prompt
        print(f"\n{choice_request.prompt}")
        
        # Display card options in a formatted box
        print(f"\n┌{'─'*68}┐")
        print(f"│ Available Options:{' '*(68 - len('Available Options:') - 1)}│")
        print(f"├{'─'*68}┤")
        for i, card in enumerate(choice_request.options):
            exhausted = "⚠ EXHAUSTED" if card.is_exhausted else ""
            eff_power = GameRules.get_effective_power(game_state, card.uuid)
            card_str = f"│  {i+1}. {card.name:<25} (Power: {eff_power:2d}) {exhausted}"
            print(f"{card_str}{' '*(69 - len(card_str))}│")
        print(f"└{'─'*68}┘")
        
        # Selection instructions
        print(f"\nSelect up to {choice_request.max_choices} card{'' if choice_request.max_choices == 1 else 's'} to {choice_request.purpose}.")
        
        # Get user input with error handling
        while True:
            try:
                indices = input("\nEnter your choice(s) (comma separated): ")
                chosen_indices = [int(idx.strip())-1 for idx in indices.split(",") if idx.strip()]
                chosen_indices = list(dict.fromkeys(chosen_indices))  # Remove duplicates preserving order
                
                # Validate choices
                if not chosen_indices and choice_request.min_choices > 0:
                    print("❌ No valid choices made. Please select at least one option.")
                    continue
                    
                if len(chosen_indices) > choice_request.max_choices:
                    print(f"❌ Too many selections. Please choose at most {choice_request.max_choices}.")
                    continue
                
                invalid_indices = [i for i in chosen_indices if i < 0 or i >= len(choice_request.options)]
                if invalid_indices:
                    print(f"❌ Invalid selection(s): {[i+1 for i in invalid_indices]}. Try again.")
                    continue
                
                # Return valid selections
                chosen = [choice_request.options[i] for i in chosen_indices]
                return chosen
                
            except ValueError:
                print("❌ Please enter valid numbers separated by commas.")