from abc import ABC, abstractmethod
from src.models.game_state import GameState
from src.models.action import Action, CardChoiceRequest
from src.models.card import Card
from typing import List, Dict

class BaseAgent(ABC):
    def __init__(self, player_id: str):
        self.player_id = player_id

    @abstractmethod
    def choose_action(self, game_state: GameState, possible_actions: List[Dict[str, Action | str]]) -> Action:
        """
        Abstract method for an agent to choose an action given the current game state and a list of possible actions.
        """
        pass

    @abstractmethod
    def choose_cards(self, game_state: GameState, choice_request: CardChoiceRequest) -> List[Card]:
        """
        Agent chooses one or more cards from the provided options for a specific purpose.
        """
        pass