from typing import Optional, List
from uuid import UUID
from src.models.card import Card

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
        return (f"AttackAction(Player: {self.player_id}, Attacking Card: {self.attacking_card_uuid})")

class BlockAction(Action):
    def __init__(self, player_id: str, blocking_card_uuid: Optional[UUID] = None):
        super().__init__(player_id)
        self.blocking_card_uuid = blocking_card_uuid # The card blocking, None if no block

    def __repr__(self):
        return (f"BlockAction(Player: {self.player_id}, Blocking Card: {self.blocking_card_uuid})")

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
    
class StealAction(Action):
    def __init__(self, player_id: str, card_uuids: List[UUID]):
        super().__init__(player_id)
        self.card_uuids = card_uuids

    def __repr__(self):
        return (f"StealAction(Player: {self.player_id}, Cards: {self.card_uuids})")
    
class PlayFromDiscardAction(Action):
    def __init__(self, player_id: str, card_uuid: UUID):
        super().__init__(player_id)
        self.card_uuid = card_uuid

    def __repr__(self):
        return (f"PlayFromDiscardAction(Player: {self.player_id}, Card: {self.card_uuid})")
    
class DiscardAction(Action):
    def __init__(self, player_id: str, card_uuids: List[UUID]):
        super().__init__(player_id)
        self.card_uuids = card_uuids

    def __repr__(self):
        return (f"DiscardAction(Player: {self.player_id}, Cards: {self.card_uuids})")
    
class DefeatAction(Action):
    def __init__(self, player_id: str, card_uuids: List[UUID]):
        super().__init__(player_id)
        self.card_uuids = card_uuids

    def __repr__(self):
        return (f"DefeatAction(Player: {self.player_id}, Cards: {self.card_uuids})")
    
class HuntAction(Action):
    def __init__(self, player_id: str, card_uuid: Optional[UUID]):
        super().__init__(player_id)
        self.card_uuid = card_uuid

    def __repr__(self):
        return (f"HuntAction(Player: {self.player_id}, Card: {self.card_uuid})")
    
class FrenzyAction(Action):
    def __init__(self, player_id: str, go_again: bool):
        super().__init__(player_id)
        self.go_again = go_again

    def __repr__(self):
        return (f"FrenzyAction(Player: {self.player_id}, Go again: {self.go_again})")

class CardChoiceRequest:
    def __init__(
        self,
        player_id: str,
        options: List[Card],
        min_choices: int,
        max_choices: int,
        purpose: str,  # e.g., "steal", "destroy", "play"
        prompt: Optional[str] = None
    ):
        self.player_id = player_id
        self.options = options
        self.min_choices = min_choices
        self.max_choices = max_choices
        self.purpose = purpose
        self.prompt = prompt or f"Choose {min_choices}-{max_choices} card(s) to {purpose}."