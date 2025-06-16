from src.agents.base_agent import BaseAgent
from src.models.game_state import GameState
from src.models.action import Action
from typing import List, Dict, Any
from src.utils.cli import MindbugCLI # Import the CLI

class HumanAgent(BaseAgent):
    def __init__(self, player_id: str):
        super().__init__(player_id)
        self.cli = MindbugCLI() # Initialize the CLI here

    def choose_action(self, game_state: GameState, possible_actions: List[Dict[str, Any]]) -> Action:
        """
        Human agent chooses an action by interacting with the CLI.
        """
        # The CLI now handles displaying the full game state
        self.cli.display_game_state(game_state)
        
        # The CLI now handles getting the action choice
        chosen_action = self.cli.get_player_action(possible_actions)
        
        return chosen_action