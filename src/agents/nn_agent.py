from src.agents.base_agent import BaseAgent
from src.models.game_state import GameState
from src.models.action import Action
from typing import List, Dict
import random

class RandomAgent(BaseAgent):
    def __init__(self, player_id: str):
        super().__init__(player_id)

    def choose_action(self, game_state: GameState, possible_actions: List[Dict[str, Action | str]]) -> Action:
        """
        Random agent chooses an action at random.
        """
        possible_action_list = [action['action'] for action in possible_actions]
        chosen_action = random.choice(possible_action_list)
        if not isinstance(chosen_action, Action):
            raise ValueError("Chosen action is not a valid Action object.")
        
        return chosen_action