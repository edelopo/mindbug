from typing import Optional

class Action:
    """Base class for all actions a player can take."""
    def __init__(self, player_id: str):
        self.player_id = player_id

    def __repr__(self):
        return f"Action(Player: {self.player_id})"

class PlayCardAction(Action):
    def __init__(self, player_id: str, card_id: str):
        super().__init__(player_id)
        self.card_id = card_id

    def __repr__(self):
        return f"PlayCardAction(Player: {self.player_id}, Card: {self.card_id})"

class AttackAction(Action):
    def __init__(self, player_id: str, attacking_creature_id: str, target_id: str):
        super().__init__(player_id)
        self.attacking_creature_id = attacking_creature_id
        self.target_id = target_id # Can be opponent's creature_id or opponent's player_id

    def __repr__(self):
        return (f"AttackAction(Player: {self.player_id}, "
                f"Attacker: {self.attacking_creature_id}, Target: {self.target_id})")

class BlockAction(Action):
    def __init__(self, player_id: str, attacking_creature_id: str, blocking_creature_id: Optional[str] = None):
        super().__init__(player_id)
        self.attacking_creature_id = attacking_creature_id # The creature being blocked
        self.blocking_creature_id = blocking_creature_id # The creature blocking, None if no block

    def __repr__(self):
        return (f"BlockAction(Player: {self.player_id}, "
                f"Attacker (to be blocked): {self.attacking_creature_id}, "
                f"Blocker: {self.blocking_creature_id if self.blocking_creature_id else 'No Block'})")

class UseMindbugAction(Action):
    def __init__(self, player_id: str, played_card_id: str):
        super().__init__(player_id)
        self.played_card_id = played_card_id # The card opponent just played

    def __repr__(self):
        return f"UseMindbugAction(Player: {self.player_id}, Target Card: {self.played_card_id})"

class PassMindbugAction(Action):
    def __init__(self, player_id: str):
        super().__init__(player_id)

    def __repr__(self):
        return f"PassMindbugAction(Player: {self.player_id})"

# Define other potential actions as needed (e.g., ActivateAbilityAction)