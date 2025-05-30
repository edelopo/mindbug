from abc import ABC, abstractmethod
from src.models.game_state import GameState
from src.models.action import Action

class BaseAgent(ABC):
    def __init__(self, player_id: str):
        self.player_id = player_id

    @abstractmethod
    def choose_action(self, game_state: GameState, possible_actions: list[Action]) -> Action:
        """
        Abstract method for an agent to choose an action given the current game state
        and a list of possible actions.
        """
        pass