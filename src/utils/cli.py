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
        Displays the current state of the game to the console.
        """
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()

        # os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for better readability

        print("\n" + "="*40)
        print(f"       TURN {game_state.turn_count} - PHASE: {game_state.phase.upper()}")
        print("="*40)

        print(f"\n--- {active_player.id} to act ---")

        print(f"\n--- {active_player.id}'s Board ---")
        print(f"Life: {active_player.life_points}, Mindbugs: {active_player.mindbugs}")
        print(f"Hand ({len(active_player.hand)} cards): {[card.name for card in active_player.hand]}")
        print(f"Cards left in deck: {len(active_player.deck)}")
        print(f"Play Area ({len(active_player.play_area)} cards):")
        if active_player.play_area:
            for card in active_player.play_area:
                exhausted_status = "(Exhausted)" if card.is_exhausted else ""
                effective_power = GameRules.get_effective_power(game_state, card.uuid)
                print(f"  - {card.name} (Power: {effective_power}) {exhausted_status}")
        else:
            print("  (Empty)")

        print(f"\n--- {inactive_player.id}'s Board ---")
        print(f"Life: {inactive_player.life_points}, Mindbugs: {inactive_player.mindbugs}")
        print(f"Hand size: {len(inactive_player.hand)}")
        print(f"Cards left in deck: {len(active_player.deck)}")
        print(f"Play Area ({len(inactive_player.play_area)} cards):")
        if inactive_player.play_area:
            for card in inactive_player.play_area:
                exhausted_status = "(Exhausted)" if card.is_exhausted else ""
                effective_power = GameRules.get_effective_power(game_state, card.uuid)
                print(f"  - {card.name} (Power: {effective_power}) {exhausted_status}")        
        else:
            print("  (Empty)")
        print("="*40 + "\n")

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
                    print("Invalid action number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    # def get_card_choice(self, choice_request: CardChoiceRequest) -> List[Card]:
    #     print(choice_request.prompt)
    #     for i, card in enumerate(choice_request.options):
    #         print(f"{i+1}: {card.name} (Power: {card.power})")
    #     indices = input(f"Enter the numbers of your choices (comma separated, up to {choice_request.max_choices}): ")
    #     chosen_indices = [int(idx.strip())-1 for idx in indices.split(",")]
    #     for idx in chosen_indices:
    #         if idx < 0 or idx >= len(choice_request.options):
    #             raise ValueError(f"Invalid choice index: {idx + 1}. Please choose from the available options.")
    #     if len(chosen_indices) > choice_request.max_choices:
    #         raise ValueError(f"Too many choices. You can only choose up to {choice_request.max_choices} cards.")
    #     chosen = [choice_request.options[i] for i in chosen_indices]
    #     return chosen

    def get_card_choice(self, choice_request: CardChoiceRequest) -> List[Card]:
        """
        Prompts the player to select cards from the given options.
        """
        print("\n" + "="*40)
        print(f"  CARD SELECTION")
        print("="*40)
        print(f"\n{choice_request.prompt}")
        
        # Display card options in a formatted way
        print("\nAvailable cards:")
        for i, card in enumerate(choice_request.options):
            print(f"  {i+1}. {card.name:<15} (Power: {card.power})")
        
        # Selection instructions
        print(f"\nSelect up to {choice_request.max_choices} card{'' if choice_request.max_choices == 1 else 's'} to {choice_request.purpose}.")
        
        # Get user input with error handling
        while True:
            try:
                indices = input("\nEnter your choice(s) (comma separated): ")
                chosen_indices = [int(idx.strip())-1 for idx in indices.split(",") if idx.strip()]
                
                # Validate choices
                if not chosen_indices:
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