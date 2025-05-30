from src.agents.base_agent import BaseAgent
from src.models.game_state import GameState
from src.models.action import (
    Action, PlayCardAction, AttackAction,
    UseMindbugAction, PassMindbugAction, BlockAction
)
from uuid import UUID

class HumanAgent(BaseAgent):
    def choose_action(self, game_state: GameState, possible_actions: list[Action]) -> Action:
        active_player = game_state.get_active_player()
        print(f"\n--- {active_player.id}'s Turn (Phase: {game_state.phase}) ---")
        print(f"Your Hand: {[f'{card.name} (UUID: {str(card.uuid)[:4]}...)' for card in active_player.hand]}")
        print(f"Your Play Area: {[f'{card.name} (P:{card.power}, Exhausted: {card.is_exhausted})' for card in active_player.play_area]}")
        print(f"Your Life: {active_player.life_points}, Mindbugs: {active_player.mindbugs}")

        inactive_player = game_state.get_inactive_player()
        print(f"Opponent's Play Area: {[f'{card.name} (P:{card.power})' for card in inactive_player.play_area]}")
        print(f"Opponent's Life: {inactive_player.life_points}, Mindbugs: {inactive_player.mindbugs}")

        print("\nPossible actions:")
        for i, action in enumerate(possible_actions):
            print(f"{i + 1}. {action}")

        while True:
            try:
                choice = input("Enter the number of your chosen action: ")
                action_index = int(choice) - 1
                if 0 <= action_index < len(possible_actions):
                    return possible_actions[action_index]
                else:
                    print("Invalid action number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")