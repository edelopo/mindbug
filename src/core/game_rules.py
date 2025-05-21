from typing import Dict, List, Optional, Tuple
from src.models.game_state import GameState
from src.models.card import Card
from src.models.action import Action # Will use this to validate actions later

class GameRules:
    def __init__(self, card_definitions: Dict[str, Card]):
        self.card_definitions = card_definitions
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
            # ... add more keywords
        }

    # --- Core Game Logic Functions ---

    def resolve_combat(self, game_state: GameState, attacker_creature: Creature, blocker_creature: Creature) -> Tuple[GameState, Optional[str]]:
        """
        Resolves a combat between two creatures.
        Returns the updated GameState and the ID of the defeated creature(s) or None if none.
        Note: This simplifies for now. Mindbug has simultaneous defeats.
        """
        print(f"Resolving combat: {attacker_creature.name} (P:{attacker_creature.current_power}) vs {blocker_creature.name} (P:{blocker_creature.current_power})")

        defeated_attackers = []
        defeated_blockers = []

        # Check for Poisonous keyword first
        if "Poisonous" in attacker_creature.keywords:
            print(f"{attacker_creature.name} is Poisonous. {blocker_creature.name} is defeated.")
            defeated_blockers.append(blocker_creature.id)
            
        if "Poisonous" in blocker_creature.keywords:
            print(f"{blocker_creature.name} is Poisonous. {attacker_creature.name} is defeated.")
            defeated_attackers.append(attacker_creature.id)

        # Normal power comparison if not already defeated by Poisonous
        if attacker_creature.id not in defeated_attackers and blocker_creature.id not in defeated_blockers:
            if attacker_creature.current_power > blocker_creature.current_power:
                defeated_blockers.append(blocker_creature.id)
                print(f"{attacker_creature.name} defeats {blocker_creature.name}.")
            elif blocker_creature.current_power > attacker_creature.current_power:
                defeated_attackers.append(attacker_creature.id)
                print(f"{blocker_creature.name} defeats {attacker_creature.name}.")
            else: # Equal power
                defeated_attackers.append(attacker_creature.id)
                defeated_blockers.append(blocker_creature.id)
                print(f"{attacker_creature.name} and {blocker_creature.name} defeat each other.")

        # Apply "Tough" keyword effect
        # Tough: If this creature would be defeated, and is not yet exhausted (sideways), exhaust it by turning it sideways.
        # It otherwise works completely normally. If it gets defeated while exhausted, it is discarded.
        # This means 'Tough' effectively gives a creature a second life by becoming exhausted instead of discarded.
        
        # NOTE: This implementation of Tough assumes a simple defeat process.
        # A more complex rule might involve 'damage' and then 'defeated by damage'
        # For simplicity, if 'Tough' is present, and creature is not exhausted, it becomes exhausted instead of defeated.
        # If it's already exhausted, it's defeated.
        
        # Apply Tough for attacker
        if attacker_creature.id in defeated_attackers and "Tough" in attacker_creature.keywords:
            if not attacker_creature.is_exhausted:
                attacker_creature.is_exhausted = True
                print(f"{attacker_creature.name} is Tough. It becomes exhausted instead of defeated.")
                defeated_attackers.remove(attacker_creature.id) # Prevent actual defeat
            else:
                print(f"{attacker_creature.name} is Tough and already exhausted. It is defeated.")
                # It remains in defeated_attackers, will be removed from battlefield

        # Apply Tough for blocker
        if blocker_creature.id in defeated_blockers and "Tough" in blocker_creature.keywords:
            if not blocker_creature.is_exhausted:
                blocker_creature.is_exhausted = True
                print(f"{blocker_creature.name} is Tough. It becomes exhausted instead of defeated.")
                defeated_blockers.remove(blocker_creature.id) # Prevent actual defeat
            else:
                print(f"{blocker_creature.name} is Tough and already exhausted. It is defeated.")
                # It remains in defeated_blockers, will be removed from battlefield


        # Remove defeated creatures from battlefield and move to owner's discard pile
        # Important: Creatures go to their *owner's* discard pile, even if controlled by opponent.
        # For now, let's assume they go to the *controller's* discard pile for simplicity,
        # but Mindbug rules usually define an 'owner' vs 'controller'.
        # For now, let's just make it simple and put to current controller's discard.
        
        # This will require finding the creature by ID on the battlefield
        # and then moving it to the correct player's discard pile.
        # This usually implies modifying the game_state in place, or passing it back.
        
        # This function should probably return the list of creatures that were defeated.
        # The GameEngine then handles the state update.
        
        return game_state, (defeated_attackers, defeated_blockers) # Return a tuple of defeated IDs


    def lose_life(self, game_state: GameState, player_id: str, amount: int = 1) -> GameState:
        """A player loses life."""
        player_losing_life = game_state.get_player(player_id)
        
        # In Mindbug, life is represented by the opponent's unused pile
        # So, if Player A loses life, a card is removed from Player B's unused pile
        # Let's clarify this rule:
        # "Whenever you lose a life point, remove one of your life tracking cards from the game."
        # This implies each player tracks their own life points with cards from the unused pile.
        # We need to adjust GameState and Player to reflect this.

        # Let's adjust: GameState should distribute initial unused cards to players for life.
        # Or, we can simply track life points (e.g., int) on the Player object,
        # which is usually simpler than managing a separate pile of cards.
        # Let's make a decision: Simpler to track `life_points: int` on Player.

        # FOR NOW, let's assume `Player` has a `life_points` attribute.
        # (This will require updating Player class again)

        # TEMPORARY: For the current GameState/Player:
        # If `unused_pile` in `GameState` is the *central pool of cards for life*
        # and `player.unused_pile_for_life` is not a thing, then this means:
        # "Losing life" means discarding a card from the *opponent's* unused pile.
        # This is a key Mindbug mechanic.
        
        # Let's assume life points are tracked by cards in `player.life_cards`
        # which were drawn from `game_state.unused_pile` at the start.
        # This means `initial_state` needs modification to populate `player.life_cards`.
        # And `GameState.unused_pile` would be the *leftover* pool.

        # For the purpose of *this* example, let's simplify and make the `unused_pile` in `GameState`
        # act as the *total life pool for the game*, and players lose from it.
        # This is a simplification and not perfectly aligned with Mindbug.
        # REAL MINDBUG: each player takes 3 cards from the unused pile as their life.
        # Let's implement it the real Mindbug way then!
        # Requires Player.life_cards: List[Card] and GameState.initial_state to fill it.

        # REVISING based on true Mindbug rules (from search):
        # "Each player starts the game with 3 life points. To track life points, take 3 cards
        # from the remaining pile of unused cards (the pile of 28 cards that have not been
        # dealt to players) and place them face down in front of the player."
        # "Whenever you lose a life point, remove one of your life tracking cards from the game."

        player_losing_life = game_state.get_player(player_id)
        for _ in range(amount):
            if player_losing_life.life_cards: # Assuming Player has life_cards
                lost_card = player_losing_life.life_cards.pop()
                game_state.discard_pile.append(lost_card) # Or remove from game
                print(f"{player_losing_life.player_id} loses 1 life point.")
            else:
                # Player has no life points left, they lose the game
                game_state.game_over = True
                game_state.winner_id = game_state.inactive_player_id if player_id == game_state.active_player_id else game_state.active_player_id
                print(f"{player_losing_life.player_id} has no life points left! {game_state.winner_id} wins!")
                break # No more life to lose

        return game_state

    # --- Ability Handlers (called by GameEngine when appropriate) ---

    def activate_play_ability(self, game_state: GameState, creature_played: Creature, player_who_played_id: str) -> GameState:
        """Activates a creature's 'Play' ability."""
        print(f"Activating Play ability for {creature_played.name} (played by {player_who_played_id})")
        handler = self.play_ability_handlers.get(creature_played.id)
        if handler:
            # Pass only necessary information; might need to pass creature_played object if ability modifies it
            game_state = handler(game_state.copy(), creature_played, player_who_played_id) # Pass a copy to avoid side effects if modifying state in handler
        return game_state

    def activate_attack_ability(self, game_state: GameState, attacking_creature: Creature) -> GameState:
        """Activates a creature's 'Attack' ability."""
        print(f"Activating Attack ability for {attacking_creature.name}")
        handler = self.attack_ability_handlers.get(attacking_creature.id)
        if handler:
            game_state = handler(game_state.copy(), attacking_creature)
        return game_state

    def activate_defeated_ability(self, game_state: GameState, defeated_creature: Creature) -> GameState:
        """Activates a creature's 'Defeated' ability."""
        print(f"Activating Defeated ability for {defeated_creature.name}")
        handler = self.defeated_ability_handlers.get(defeated_creature.id)
        if handler:
            game_state = handler(game_state.copy(), defeated_creature)
        return game_state

    # --- Specific Card Ability Implementations ---
    # These functions take a GameState (or relevant parts) and apply the effect,
    # returning a new GameState.

    def _axolotl_healer_play_ability(self, game_state: GameState, creature: Creature, player_id: str) -> GameState:
        """Axolotl Healer's 'Play' effect: Draw a card. You gain 2 life."""
        player = game_state.get_player(player_id)
        
        # Player draws a card
        drawn_card = player.draw_card()
        if drawn_card:
            print(f"{player.player_id} draws {drawn_card.name} from Axolotl Healer.")
        else:
            print(f"{player.player_id}'s deck is empty, cannot draw card from Axolotl Healer.")

        # Player gains 2 life
        # Gaining life in Mindbug means taking cards from the central unused pile.
        # This is where GameState.unused_pile comes in.
        for _ in range(2):
            if game_state.unused_pile:
                life_card = game_state.unused_pile.pop()
                player.life_cards.append(life_card) # Add to player's life pile
                print(f"{player.player_id} gains 1 life point.")
            else:
                print(f"No more cards in central unused pile to gain life for {player.player_id}.")
                break

        return game_state

    def _tusked_extorter_attack_ability(self, game_state: GameState, attacking_creature: Creature) -> GameState:
        """Tusked Extorter's 'Attack' effect: Your opponent discards a card."""
        opponent = game_state.get_inactive_player() if attacking_creature.controller_id == game_state.active_player_id else game_state.get_active_player()
        
        if opponent.hand:
            # AI decision: which card to discard? For now, random.
            card_to_discard = random.choice(opponent.hand)
            opponent.discard_card(card_to_discard) # Assuming discard_card handles removal
            print(f"{opponent.player_id} discards {card_to_discard.name} due to Tusked Extorter.")
        else:
            print(f"{opponent.player_id}'s hand is empty, cannot discard.")

        return game_state

    # --- Keyword Handlers (e.g., during combat or blocking) ---

    def _handle_tough_keyword(self, creature: Creature):
        # This is handled directly in resolve_combat for defeat effect.
        # Could be used for other checks if 'Tough' grants other abilities.
        pass

    def _handle_poisonous_keyword(self, creature: Creature):
        # Handled in resolve_combat.
        pass

    def _handle_frenzy_keyword(self, creature: Creature):
        # This keyword affects `GameEngine`'s attack phase logic (allowing a second attack).
        # The `GameRules` wouldn't "handle" it directly, but the `GameEngine` would check for it.
        pass

    def _handle_sneaky_keyword(self, creature: Creature):
        # This keyword affects `GameEngine`'s blocking logic.
        # The `GameEngine` would filter valid blockers based on this.
        pass
    
    def _handle_hunter_keyword(self, creature: Creature):
        # This keyword affects target selection in `GameEngine`'s attack logic.
        # The `GameEngine` would offer specific creature targets instead of player for attacks.
        pass

    # --- Utility methods for rules ---
    # These might be used by GameEngine to determine valid actions or apply effects.

    def is_creature_valid_blocker(self, attacker: Creature, blocker: Creature) -> bool:
        """Checks if a blocker is valid against an attacker given keywords like Sneaky."""
        if "Sneaky" in attacker.keywords and "Sneaky" not in blocker.keywords:
            return False # Sneaky can only be blocked by Sneaky
        # Add other blocking rules if they exist (e.g., creatures that cannot block)
        return True