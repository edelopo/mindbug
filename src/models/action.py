from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.player import Card

class Action:
    """Base class for all actions a player can take."""
    def __init__(self, player_id: str):
        self.player_id = player_id

    def __repr__(self):
        return f"Action(Player: {self.player_id})"

class PlayCardAction(Action):
    def __init__(self, player_id: str, card: 'Card'):
        super().__init__(player_id)
        self.card = card

    def __repr__(self):
        return f"PlayCardAction(Player: {self.player_id}, Card: {self.card.id})"

class AttackAction(Action):
    def __init__(self, player_id: str, attacking_card_id: str, target_id: str):
        super().__init__(player_id)
        self.attacking_card_id = attacking_card_id
        self.target_id = target_id # Can be opponent's card_id or opponent's player_id

    def __repr__(self):
        return (f"AttackAction(Player: {self.player_id}, "
                f"Attacker: {self.attacking_card_id}, Target: {self.target_id})")

class BlockAction(Action):
    def __init__(self, player_id: str, attacking_card_id: str, blocking_card_id: Optional[str] = None):
        super().__init__(player_id)
        self.attacking_card_id = attacking_card_id # The card being blocked
        self.blocking_card_id = blocking_card_id # The card blocking, None if no block

    def __repr__(self):
        return (f"BlockAction(Player: {self.player_id}, "
                f"Attacker (to be blocked): {self.attacking_card_id}, "
                f"Blocker: {self.blocking_card_id if self.blocking_card_id else 'No Block'})")

class UseMindbugAction(Action):
    def __init__(self, player_id: str):
        super().__init__(player_id)

    def __repr__(self):
        return f"UseMindbugAction(Player: {self.player_id})"

class PassMindbugAction(Action):
    def __init__(self, player_id: str):
        super().__init__(player_id)

    def __repr__(self):
        return f"PassMindbugAction(Player: {self.player_id})"

# Define other potential actions as needed (e.g., ActivateAbilityAction)