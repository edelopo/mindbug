import random
import copy
from uuid import UUID
from typing import Dict, List, Optional, Tuple
from src.models.game_state import GameState
from src.models.card import Card

class GameRules:
    # We begin with "static" variables that we want to access witout instantiating the class.
    # Map card IDs to specific ability functions for "Play" effects
    play_ability_handlers = {
        "axolotl_healer": "_axolotl_healer_play_ability",
        # Add more play abilities here
    }
    # Map card IDs to specific ability functions for "Attack" effects
    attack_ability_handlers = {
        "tusked_extorter": "_tusked_extorter_attack_ability",
        # Add more attack abilities here
    }
    # Map card IDs to specific ability functions for "Defeated" effects
    defeated_ability_handlers = {
        # "some_card_id": self._some_card_defeated_ability,
    }
    # Map card IDs to specific ability functions for "Passive" effects
    passive_ability_handlers = {
        "shield_bugs": "_shield_bugs_passive_ability",
    }
    # Keyword handlers (e.g., for Tough, Frenzy, Poisonous, Sneaky, Hunter)
    keyword_handlers = {
        "Tough": "_handle_tough_keyword",
        "Poisonous": "_handle_poisonous_keyword",
        "Frenzy": "_handle_frenzy_keyword",
        "Sneaky": "_handle_sneaky_keyword",
        "Hunter": "_handle_hunter_keyword"
    }

    def __init__(self, card_definitions: Dict[str, Card], deck_size: int = 10, hand_size: int = 5):
        self.card_definitions = card_definitions
        self.deck_size = deck_size
        self.hand_size = hand_size

    # --- Core Game Logic Functions ---

    def resolve_combat(self, game_state: GameState, attacker_uuid: UUID, 
                       blocker_uuid: UUID) -> Tuple[GameState, List[UUID]]:
        """
        Resolves a combat between two cards.
        Returns the updated GameState and a list of defeated card UUIDs.
        """
        attacker = None
        for card in game_state.get_inactive_player().play_area: # The attacking player is the inactive player
            if card.uuid == attacker_uuid:
                attacker = card
                break
        else:
            raise ValueError(f"Attacker card with UUID {attacker_uuid} not found in play area.")
        
        blocker = None
        for card in game_state.get_active_player().play_area: # The defending player is the active player
            if card.uuid == blocker_uuid:
                blocker = card
                break
        else:
            raise ValueError(f"Blocker card with UUID {blocker_uuid} not found in play area.")
        
        if attacker.controller is None or blocker.controller is None:
            raise ValueError("Attacker or blocker has no controller. Cannot resolve combat.")
        
        effective_attacker_power = self.get_effective_power(game_state, attacker.uuid)
        effective_blocker_power = self.get_effective_power(game_state, blocker.uuid)

        print(f"Resolving combat: {attacker.name} (P={effective_attacker_power}) "
              f"vs {blocker.name} (P={effective_blocker_power})")

        defeated_attacker = False
        defeated_blocker = False

        # Check for Poisonous keyword first
        if "Poisonous" in attacker.keywords:
            print(f"{attacker.name} is Poisonous. {blocker.name} is defeated.")
            defeated_blocker = True
            
        if "Poisonous" in blocker.keywords:
            print(f"{blocker.name} is Poisonous. {attacker.name} is defeated.")
            defeated_attacker = True

        # Effective power comparison if not already defeated by Poisonous
        if not defeated_attacker or not defeated_blocker:
            if effective_attacker_power > effective_blocker_power:
                defeated_blocker = True
                print(f"{attacker.name} defeats {blocker.name}.")
            elif effective_blocker_power > effective_attacker_power:
                defeated_attacker = True
                print(f"{blocker.name} defeats {attacker.name}.")
            else: # Equal power
                defeated_attacker = True
                defeated_blocker = True
                print(f"{attacker.name} and {blocker.name} defeat each other.")

        # Apply Tough for attacker
        if defeated_attacker and "Tough" in attacker.keywords:
            if not attacker.is_exhausted:
                attacker.is_exhausted = True
                print(f"{attacker.name} is Tough. It becomes exhausted instead of defeated.")
                defeated_attacker = False # Prevent actual defeat
            else:
                print(f"{attacker.name} is Tough but already exhausted. It is defeated.")
                # It remains in defeated_attackers, will be removed from battlefield

        # Apply Tough for blocker
        if defeated_blocker and "Tough" in blocker.keywords:
            if not blocker.is_exhausted:
                blocker.is_exhausted = True
                print(f"{blocker.name} is Tough. It becomes exhausted instead of defeated.")
                defeated_blocker = False # Prevent actual defeat
            else:
                print(f"{blocker.name} is Tough but already exhausted. It is defeated.")
                # It remains in defeated_blockers, will be removed from battlefield

        # Remove defeated cards from battlefield and move to controller's discard pile
        if defeated_attacker:
            attacker.controller.discard_pile.append(attacker)
            attacker.controller.play_area.remove(attacker)

        if defeated_blocker:
            blocker.controller.discard_pile.append(blocker)
            blocker.controller.play_area.remove(blocker)
        
        defeated_cards_uuid = []
        if defeated_attacker:
            defeated_cards_uuid.append(attacker.uuid)
        if defeated_blocker:
            defeated_cards_uuid.append(blocker.uuid)
        return game_state, defeated_cards_uuid


    def lose_life(self, game_state: GameState, player_id: str, amount: int = 1) -> GameState:
        """A player loses life."""
        player_losing_life = game_state.get_player(player_id)
        player_losing_life.life_points -= amount
        print(f"{player_id} loses {amount} life points, now they have {player_losing_life.life_points} life points left.")

        if player_losing_life.life_points <= 0:
            # Player has no life points left, they lose the game
            game_state.game_over = True
            if player_id == game_state.active_player_id:
                game_state.winner_id = game_state.inactive_player_id
            else:
                game_state.winner_id = game_state.active_player_id
            print(f"{player_id} has no life points left! {game_state.winner_id} wins!")

        return game_state


    # --- Ability Handlers (called by GameEngine when appropriate) ---

    def activate_play_ability(self, game_state: GameState, card_played_uuid: UUID) -> GameState:
        """Activates a card's 'Play' ability."""
        card_played = self.get_card_by_uuid(game_state, card_played_uuid)
        if card_played.controller is None:
            raise ValueError(f"Card with UUID {card_played_uuid} has no controller. Cannot activate play ability.")
        if card_played.ability_type == "play":
            print(f"Activating Play ability of {card_played.name} for {card_played.controller.id}")
            handler_name = self.play_ability_handlers.get(card_played.id)
            if handler_name:
                handler = getattr(self, handler_name)
                game_state = handler(copy.deepcopy(game_state), card_played_uuid)
        return game_state

    def activate_attack_ability(self, game_state: GameState, attacking_card_uuid: UUID) -> GameState:
        """Activates a card's 'Attack' ability."""
        attacking_card = self.get_card_by_uuid(game_state, attacking_card_uuid)
        if attacking_card.controller is None:
            raise ValueError(f"Attacking card with UUID {attacking_card_uuid} has no controller. Cannot activate attack ability.")
        if attacking_card.ability_type == "attack":
            print(f"Activating Attack ability for {attacking_card.name}")
            handler_name = self.attack_ability_handlers.get(attacking_card.id)
            if handler_name:
                handler = getattr(self, handler_name)
                game_state = handler(copy.deepcopy(game_state), attacking_card_uuid)
        return game_state

    def activate_defeated_ability(self, game_state: GameState, defeated_card_uuid: UUID) -> GameState:
        """Activates a card's 'Defeated' ability."""
        defeated_card = self.get_card_by_uuid(game_state, defeated_card_uuid)
        if defeated_card.controller is None:
            raise ValueError(f"Defeated card with UUID {defeated_card_uuid} has no controller. Cannot activate defeated ability.")
        if defeated_card.ability_type == "defeated":
            print(f"Activating Defeated ability for {defeated_card.name}")
            handler_name = self.defeated_ability_handlers.get(defeated_card.id)
            if handler_name:
                handler = getattr(self, handler_name)
                game_state = handler(copy.deepcopy(game_state), defeated_card_uuid)
        return game_state


    # --- Specific Card Ability Implementations ---
    # These functions take a GameState (or relevant parts) and apply the effect,
    # returning a new GameState.

    # -- Play Abilities --

    @staticmethod
    def _axolotl_healer_play_ability(game_state: GameState, card_uuid: UUID) -> GameState:
        """Axolotl Healer's 'Play' effect: Gain 2 life points."""
        card_played = GameRules.get_card_by_uuid(game_state, card_uuid)
        player = card_played.controller
        if player is None:
            raise ValueError("Card played has no controller. Cannot resolve play ability.")

        # Player gains 2 life
        player.life_points += 2
        print(f"{player.id} gains 2 life points. New life: {player.life_points}")

        return game_state
    
    # -- Attack Abilities --

    @staticmethod
    def _tusked_extorter_attack_ability(game_state: GameState, attacking_card_uuid: UUID) -> GameState:
        """Tusked Extorter's 'Attack' effect: The opponent discards a card."""
        attacking_card = GameRules.get_card_by_uuid(game_state, attacking_card_uuid)
        if attacking_card.controller is None:
            raise ValueError("Attacking card has no controller. Cannot resolve attack ability.")
        
        opponent = game_state.get_opponent_of(attacking_card.controller.id)
        
        if opponent.hand:
            # AI/Player decision: which card to discard? For now, random.
            card_to_discard = random.choice(opponent.hand)
            opponent.discard_card(card_to_discard)
            print(f"{opponent.id} discards {card_to_discard.name} due to Tusked Extorter.")
        else:
            print(f"{opponent.id}'s hand is empty, cannot discard.")

        return game_state
    
    # -- Defeated Abilities --

    # -- Passive Abilities --
    # Some of these are handled at the relevant part of the game logic, such as is_valid_blocker or resolve_combat.

    @staticmethod
    def _shield_bugs_passive_ability(game_state: GameState, shield_bugs_uuid: UUID, 
                                     affected_card_uuid: UUID) -> int:
        """Shield Bugs' 'Passive' effect: Other allied creatures have +1 power."""
        shield_bugs_card = GameRules.get_card_by_uuid(game_state, shield_bugs_uuid)
        if shield_bugs_card.controller is None:
            raise ValueError("Shield Bugs card has no controller. Cannot resolve passive ability.")
        affected_card = GameRules.get_card_by_uuid(game_state, affected_card_uuid)
        if affected_card.controller is None:
            raise ValueError("Affected card has no controller. Cannot resolve passive ability.")
        if (affected_card.controller.id == shield_bugs_card.controller.id
            and affected_card.uuid != shield_bugs_uuid):
            return 1
        else:
            return 0


    # --- Keyword Handlers (e.g., during combat or blocking) ---


    def _handle_tough_keyword(self, card: Card):
        # This is handled directly in resolve_combat for defeat effect.
        # Could be used for other checks if 'Tough' grants other abilities.
        pass

    def _handle_poisonous_keyword(self, card: Card):
        # Handled in resolve_combat.
        pass

    def _handle_frenzy_keyword(self, card: Card):
        # This keyword affects `GameEngine`'s attack phase logic (allowing a second attack).
        # The `GameRules` wouldn't "handle" it directly, but the `GameEngine` would check for it.
        pass

    def _handle_sneaky_keyword(self, card: Card):
        # This keyword affects `GameEngine`'s blocking logic.
        # The `GameEngine` would filter valid blockers based on this.
        pass
    
    def _handle_hunter_keyword(self, card: Card):
        # This keyword affects target selection in `GameEngine`'s attack logic.
        # The `GameEngine` would offer specific card targets instead of player for attacks.
        pass

    # --- Utility methods for rules ---
    # These might be used by GameEngine to determine valid actions or apply effects.

    def is_valid_blocker(self, blocking_card: Card, attacking_card: Card,
                              blocking_player_play_area: List[Card], 
                              attacking_player_play_area: List[Card]) -> bool:
        """Checks if a blocker is valid."""

        if "Sneaky" in attacking_card.keywords and "Sneaky" not in blocking_card.keywords:
            return False # Sneaky can only be blocked by Sneaky
        # Add other blocking rules if they exist (e.g., cards that cannot block)
        return True
    
    @staticmethod
    def get_card_by_uuid(game_state: GameState, card_uuid: UUID) -> Card:
        """Returns a card by its UUID from the game state."""
        for player in [game_state.get_active_player(), game_state.get_inactive_player()]:
            for card in player.play_area + player.hand + player.discard_pile:
                if card.uuid == card_uuid:
                    return card
        else:
            raise ValueError(f"Card with UUID {card_uuid} not found in game state.")
    
    @staticmethod
    def get_effective_power(game_state: GameState, card_uuid: UUID) -> int:
        """Returns the effective power of a card, considering any passive effects."""
        card = GameRules.get_card_by_uuid(game_state, card_uuid)
        effective_power = card.power

        for other_card in game_state.get_active_player().play_area + game_state.get_inactive_player().play_area:
            if other_card.ability_type == "passive":
                handler_name = GameRules.passive_ability_handlers.get(other_card.id)
                if handler_name:
                    handler = getattr(GameRules, handler_name)
                    effective_power += handler(game_state, other_card.uuid, card.uuid)
        
        return effective_power
        