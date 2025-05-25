import random
from typing import Dict, List, Optional, Tuple
from src.models.game_state import GameState
from src.models.card import Card
from src.models.action import Action # Will use this to validate actions later

class GameRules:
    def __init__(self, card_definitions: Dict[str, Card], deck_size: int = 10, hand_size: int = 5):
        self.card_definitions = card_definitions
        self.deck_size = deck_size
        self.hand_size = hand_size
        # Map card IDs to specific ability functions for "Play" effects
        # You'll expand this significantly as you add more cards
        self.play_ability_handlers = {
            "axolotl_healer": self._axolotl_healer_play_ability,
            # Add more play abilities here
        }
        # Map card IDs to specific ability functions for "Attack" effects
        self.attack_ability_handlers = {
            "tusked_extorter": self._tusked_extorter_attack_ability,
            # Add more attack abilities here
        }
        # Map card IDs to specific ability functions for "Defeated" effects
        self.defeated_ability_handlers = {
            # "some_card_id": self._some_card_defeated_ability,
        }
        # Keyword handlers (e.g., for Tough, Frenzy, Poisonous, Sneaky, Hunter)
        self.keyword_handlers = {
            "Tough": self._handle_tough_keyword,
            "Poisonous": self._handle_poisonous_keyword,
            "Frenzy": self._handle_frenzy_keyword,
            "Sneaky": self._handle_sneaky_keyword,
            "Hunter": self._handle_hunter_keyword,
        }

    # --- Core Game Logic Functions ---

    def resolve_combat(self, game_state: GameState, attacker: Card, blocker: Card) -> Tuple[GameState, Optional[List[Card]]]:
        """
        Resolves a combat between two cards.
        Returns the updated GameState and the ID of the defeated card(s) or None if none.
        Note: This simplifies for now. Mindbug has simultaneous defeats.
        """
        if attacker.controller == None:
            raise ValueError("Attacker has no controller. Cannot resolve combat.")
        if blocker.controller == None:
            raise ValueError("Blocker has no controller. Cannot resolve combat.")
        if attacker.controller.id != game_state.active_player_id:
            raise ValueError("Invalid attack: Attacker is not controlled by the active player.")

        print(f"Resolving combat: {attacker.name} (P:{attacker.power}) vs {blocker.name} (P:{blocker.power})")

        defeated_attacker = False
        defeated_blocker = False

        # Check for Poisonous keyword first
        if "Poisonous" in attacker.keywords:
            print(f"{attacker.name} is Poisonous. {blocker.name} is defeated.")
            defeated_blocker = True
            
        if "Poisonous" in blocker.keywords:
            print(f"{blocker.name} is Poisonous. {attacker.name} is defeated.")
            defeated_attacker = True

        # Normal power comparison if not already defeated by Poisonous
        if not defeated_attacker or not defeated_blocker:
            if attacker.power > blocker.power:
                defeated_blocker = True
                print(f"{attacker.name} defeats {blocker.name}.")
            elif blocker.power > attacker.power:
                defeated_attacker = True
                print(f"{blocker.name} defeats {attacker.name}.")
            else: # Equal power
                defeated_attacker = True
                defeated_blocker = True
                print(f"{attacker.name} and {blocker.name} defeat each other.")

        # Apply "Tough" keyword effect
        # Tough: If this card would be defeated, and is not yet exhausted (sideways), exhaust it by turning it sideways.
        # It otherwise works completely normally. If it gets defeated while exhausted, it is discarded.
        # This means 'Tough' effectively gives a card a second life by becoming exhausted instead of discarded.

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
        
        defeated_cards = []
        if defeated_attacker:
            defeated_cards.append(attacker)
        if defeated_blocker:
            defeated_cards.append(blocker)
        return game_state, defeated_cards


    def lose_life(self, game_state: GameState, player_id: str, amount: int = 1) -> GameState:
        """A player loses life."""
        player_losing_life = game_state.get_player(player_id)
        player_losing_life.life_points -= amount
        print(f"{player_id} loses {amount} life points.")

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

    def activate_play_ability(self, game_state: GameState, card_played: Card, player_who_played_id: str) -> GameState:
        """Activates a card's 'Play' ability."""
        print(f"Activating Play ability of {card_played.name} for {player_who_played_id}")
        handler = self.play_ability_handlers.get(card_played.id)
        if handler:
            # Pass only necessary information; might need to pass card_played object if ability modifies it
            game_state = handler(game_state.copy(), card_played, player_who_played_id) # Pass a copy to avoid side effects if modifying state in handler
        return game_state

    def activate_attack_ability(self, game_state: GameState, attacking_card: Card) -> GameState:
        """Activates a card's 'Attack' ability."""
        print(f"Activating Attack ability for {attacking_card.name}")
        handler = self.attack_ability_handlers.get(attacking_card.id)
        if handler:
            game_state = handler(game_state.copy(), attacking_card)
        return game_state

    def activate_defeated_ability(self, game_state: GameState, defeated_card: Card) -> GameState:
        """Activates a card's 'Defeated' ability."""
        print(f"Activating Defeated ability for {defeated_card.name}")
        handler = self.defeated_ability_handlers.get(defeated_card.id)
        if handler:
            game_state = handler(game_state.copy(), defeated_card)
        return game_state

    # --- Specific Card Ability Implementations ---
    # These functions take a GameState (or relevant parts) and apply the effect,
    # returning a new GameState.

    def _axolotl_healer_play_ability(self, game_state: GameState, card: Card, player_id: str) -> GameState:
        """Axolotl Healer's 'Play' effect: Gain 2 life points."""
        player = game_state.get_player(player_id)

        # Player gains 2 life
        player.life_points += 2
        print(f"{player_id} gains 2 life points. New life: {player.life_points}")

        return game_state

    def _tusked_extorter_attack_ability(self, game_state: GameState, attacking_card: Card) -> GameState:
        """Tusked Extorter's 'Attack' effect: The opponent discards a card."""
        if attacking_card.controller is None:
            raise ValueError("Attacking card has no controller. Cannot resolve attack ability.")
        
        opponent = game_state.get_inactive_player() if attacking_card.controller.id == game_state.active_player_id else game_state.get_active_player()
        
        if opponent.hand:
            # AI/Player decision: which card to discard? For now, random.
            card_to_discard = random.choice(opponent.hand)
            opponent.discard_card(card_to_discard)
            print(f"{opponent.id} discards {card_to_discard.name} due to Tusked Extorter.")
        else:
            print(f"{opponent.id}'s hand is empty, cannot discard.")

        return game_state

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

    def is_card_valid_blocker(self, attacker: Card, blocker: Card) -> bool:
        """Checks if a blocker is valid against an attacker given keywords like Sneaky."""
        if "Sneaky" in attacker.keywords and "Sneaky" not in blocker.keywords:
            return False # Sneaky can only be blocked by Sneaky
        # Add other blocking rules if they exist (e.g., cards that cannot block)
        return True