# CLI = Command Line Interface
from src.models.game_state import GameState
from src.models.action import Action
from typing import List, Dict
import os

class MindbugCLI:
    def display_game_state(self, game_state: GameState):
        """
        Displays the current state of the game to the console.
        """
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()

        os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for better readability

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
            for creature in active_player.play_area:
                exhausted_status = "(Exhausted)" if creature.is_exhausted else ""
                print(f"  - {creature.name} (Power: {creature.power}) {exhausted_status}")
        else:
            print("  (Empty)")

        print(f"\n--- {inactive_player.id}'s Board ---")
        print(f"Life: {inactive_player.life_points}, Mindbugs: {inactive_player.mindbugs}")
        print(f"Hand size: {len(inactive_player.hand)}")
        print(f"Cards left in deck: {len(active_player.deck)}")
        print(f"Play Area ({len(inactive_player.play_area)} cards):")
        if inactive_player.play_area:
            for creature in inactive_player.play_area:
                print(f"  - {creature.name} (Power: {creature.power})")
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