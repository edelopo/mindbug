from typing import Optional
from uuid import UUID

class Action:
    """Base class for all actions a player can take."""
    def __init__(self, player_id: str):
        self.player_id = player_id

    def __repr__(self):
        return f"Action(Player: {self.player_id})"

class PlayCardAction(Action):
    def __init__(self, player_id: str, card_uuid: UUID):
        super().__init__(player_id)
        self.card_uuid = card_uuid

    def __repr__(self):
        return f"PlayCardAction(Player: {self.player_id})"

class AttackAction(Action):
    def __init__(self, player_id: str, attacking_card_uuid: UUID):
        super().__init__(player_id)
        self.attacking_card_uuid = attacking_card_uuid

    def __repr__(self):
        return (f"AttackAction(Player: {self.player_id})")

class BlockAction(Action):
    def __init__(self, player_id: str, blocking_card_uuid: Optional[UUID] = None):
        super().__init__(player_id)
        self.blocking_card_uuid = blocking_card_uuid # The card blocking, None if no block

    def __repr__(self):
        return (f"BlockAction(Player: {self.player_id})")

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