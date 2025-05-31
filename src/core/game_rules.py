import random
import copy
from uuid import UUID
from typing import List, Tuple, Dict
from src.models.game_state import GameState
from src.models.card import Card

# --- Core Game Logic Functions ---

def defeat(game_state: GameState, card_uuid: UUID) -> Tuple[GameState, bool]:
    """
    Defeats a card by moving it from play area to discard pile.
    It includes Tough keyword handling.
    Returns the updated GameState.
    """
    card = get_card_by_uuid(game_state, card_uuid)
    if card.controller is None:
        raise ValueError("Card has no controller. Cannot defeat.")   

    defeated = True
    # Apply Tough
    if "Tough" in card.keywords and not card.is_exhausted:
        print(f"{card.name} is Tough. It becomes exhausted instead of defeated.")
        card.is_exhausted = True
        defeated = False
    else:
        # Remove defeated card from play area and move to controller's discard pile
        card.controller.discard_pile.append(card)
        card.controller.play_area.remove(card)
    return (game_state, defeated)

def resolve_combat(game_state: GameState, attacker_uuid: UUID, 
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
    
    effective_attacker_power = get_effective_power(game_state, attacker.uuid)
    effective_blocker_power = get_effective_power(game_state, blocker.uuid)

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

    if defeated_attacker:
        game_state, defeated_attacker = defeat(game_state, attacker.uuid)
    if defeated_blocker:
        game_state, defeated_blocker = defeat(game_state, blocker.uuid)
    
    # We have to do this twice because the defeat function may change the bool value of defeated
    defeated_cards_uuid = []
    if defeated_attacker:
        defeated_cards_uuid.append(attacker.uuid)
    if defeated_blocker:
        defeated_cards_uuid.append(blocker.uuid)
    return game_state, defeated_cards_uuid


    # --- Ability Handlers (called by GameEngine when appropriate) ---

def activate_play_ability(game_state: GameState, card_played_uuid: UUID, agents: Dict = {}) -> GameState:
    """Activates a card's 'Play' ability."""
    card_played = get_card_by_uuid(game_state, card_played_uuid)
    if card_played.controller is None:
        raise ValueError(f"Card with UUID {card_played_uuid} has no controller. Cannot activate play ability.")
    if card_played.ability_type == "play":
        print(f"Activating Play ability of {card_played.name} for {card_played.controller.id}")
        handler = play_ability_handlers.get(card_played.id)
        if handler:
            game_state = handler(copy.deepcopy(game_state), card_played_uuid, agents)
    return game_state

def activate_attack_ability(game_state: GameState, attacking_card_uuid: UUID, agents: Dict = {}) -> GameState:
    """Activates a card's 'Attack' ability."""
    attacking_card = get_card_by_uuid(game_state, attacking_card_uuid)
    if attacking_card.controller is None:
        raise ValueError(f"Attacking card with UUID {attacking_card_uuid} has no controller. Cannot activate attack ability.")
    if attacking_card.ability_type == "attack":
        print(f"Activating Attack ability for {attacking_card.name}")
        handler = attack_ability_handlers.get(attacking_card.id)
        if handler:
            game_state = handler(copy.deepcopy(game_state), attacking_card_uuid, agents)
    return game_state

def activate_defeated_ability(game_state: GameState, defeated_card_uuid: UUID, agents: Dict = {}) -> GameState:
    """Activates a card's 'Defeated' ability."""
    defeated_card = get_card_by_uuid(game_state, defeated_card_uuid)
    if defeated_card.controller is None:
        raise ValueError(f"Defeated card with UUID {defeated_card_uuid} has no controller. Cannot activate defeated ability.")
    if defeated_card.ability_type == "defeated":
        print(f"Activating Defeated ability for {defeated_card.name}")
        handler = defeated_ability_handlers.get(defeated_card.id)
        if handler:
            game_state = handler(copy.deepcopy(game_state), defeated_card_uuid, agents)
    return game_state


# --- Specific Card Ability Implementations ---
# These functions take a GameState (or relevant parts) and apply the effect,
# returning a new GameState.

# -- Play Abilities --

def _axolotl_healer_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict = {}) -> GameState:
    """Axolotl Healer's 'Play' effect: Gain 2 life points."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    player = card_played.controller
    if player is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")

    # Player gains 2 life
    player.life_points += 2
    print(f"{player.id} gains 2 life points. New life: {player.life_points}")

    return game_state

def _kangasaurus_rex_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict = {}) -> GameState:
    """Kangasaurus Rex's 'Play' effect: Defeat all enemy creatures with power 4 or less.."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    opponent = game_state.get_opponent_of(card_played.controller.id)
    for card in opponent.play_area:
        effective_power = get_effective_power(game_state, card.uuid)
        if effective_power <= 4:
            print(f"{card.name} (P={effective_power}) is defeated by Kangasaurus Rex.")
            game_state, defeated = defeat(game_state, card.uuid)
    return game_state

# -- Attack Abilities --

def _tusked_extorter_attack_ability(game_state: GameState, attacking_card_uuid: UUID, agents: Dict = {}) -> GameState:
    """Tusked Extorter's 'Attack' effect: The opponent discards a card."""
    attacking_card = get_card_by_uuid(game_state, attacking_card_uuid)
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

def _harpy_mother_defeated_ability(game_state: GameState, defeated_card_uuid: UUID, agents: Dict = {}) -> GameState:
    """Harpy Mother's 'Defeated' effect: Take control of up to two creatures with power 5 or less."""
    defeated_card = get_card_by_uuid(game_state, defeated_card_uuid)
    if defeated_card.controller is None:
        raise ValueError("Defeated card has no controller. Cannot resolve defeated ability.")
    
    player = defeated_card.controller
    opponent = game_state.get_opponent_of(player.id)

    valid_targets = []
    for card in opponent.play_area:
        effective_power = get_effective_power(game_state, card.uuid)
        if effective_power <= 5:
            valid_targets.append(card)

    if not valid_targets:
        print(f"No valid creatures with power 5 or less to take control of.")
        return game_state
    # Create a choice request
    from src.models.action import CardChoiceRequest
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=valid_targets,
        min_choices=1,
        max_choices=min(2, len(valid_targets)),
        purpose="steal",
        prompt="Choose up to two creatures with power 5 or less to steal."
    )

    # Ask the agent to choose
    agent = agents[player.id]
    chosen_cards = agent.choose_cards(game_state, choice_request)

    # Steal the chosen cards
    for card in chosen_cards:
        opponent.play_area.remove(card)
        player.play_area.append(card)
        card.controller = player
        print(f"{player.id} steals {card.name} from {opponent.id}.")

    return game_state

# -- Passive Abilities --
# Some of these are handled at the relevant part of the game logic, such as is_valid_blocker or resolve_combat.

def _shield_bugs_passive_ability(game_state: GameState, shield_bugs_uuid: UUID, 
                                    affected_card_uuid: UUID, agents: Dict = {}) -> int:
    """Shield Bugs' 'Passive' effect: Other allied creatures have +1 power."""
    shield_bugs_card = get_card_by_uuid(game_state, shield_bugs_uuid)
    if shield_bugs_card.controller is None:
        raise ValueError("Shield Bugs card has no controller. Cannot resolve passive ability.")
    affected_card = get_card_by_uuid(game_state, affected_card_uuid)
    if affected_card.controller is None:
        raise ValueError("Affected card has no controller. Cannot resolve passive ability.")
    if (affected_card.controller.id == shield_bugs_card.controller.id
        and affected_card.uuid != shield_bugs_uuid):
        return 1
    else:
        return 0


# --- Keyword Handlers (e.g., during combat or blocking) ---

def _handle_tough_keyword(card: Card):
    # This is handled directly in resolve_combat for defeat effect.
    # Could be used for other checks if 'Tough' grants other abilities.
    pass

def _handle_poisonous_keyword(card: Card):
    # Handled in resolve_combat.
    pass

def _handle_frenzy_keyword(card: Card):
    # This keyword affects `GameEngine`'s attack phase logic (allowing a second attack).
    # The `GameRules` wouldn't "handle" it directly, but the `GameEngine` would check for it.
    pass

def _handle_sneaky_keyword(card: Card):
    # This keyword affects `GameEngine`'s blocking logic.
    # The `GameEngine` would filter valid blockers based on this.
    pass

def _handle_hunter_keyword(card: Card):
    # This keyword affects target selection in `GameEngine`'s attack logic.
    # The `GameEngine` would offer specific card targets instead of player for attacks.
    pass

# --- Dicts of Ability Handlers ---

# Map card IDs to specific ability functions for "Play" effects
play_ability_handlers = {
    "axolotl_healer": _axolotl_healer_play_ability,
    "kangasaurus_rex": _kangasaurus_rex_play_ability,
}
# Map card IDs to specific ability functions for "Attack" effects
attack_ability_handlers = {
    "tusked_extorter": _tusked_extorter_attack_ability,
    # Add more attack abilities here
}
# Map card IDs to specific ability functions for "Defeated" effects
defeated_ability_handlers = {
    # "some_card_id": self._some_card_defeated_ability,
}
# Map card IDs to specific ability functions for "Passive" effects
passive_ability_handlers = {
    "shield_bugs": _shield_bugs_passive_ability,
}
# Keyword handlers (e.g., for Tough, Frenzy, Poisonous, Sneaky, Hunter)
keyword_handlers = {
    "Tough": _handle_tough_keyword,
    "Poisonous": _handle_poisonous_keyword,
    "Frenzy": _handle_frenzy_keyword,
    "Sneaky": _handle_sneaky_keyword,
    "Hunter": _handle_hunter_keyword
}

# --- Utility methods for rules ---
# These might be used by GameEngine to determine valid actions or apply effects.

def is_valid_blocker(blocking_card: Card, attacking_card: Card,
                            blocking_player_play_area: List[Card], 
                            attacking_player_play_area: List[Card]) -> bool:
    """Checks if a blocker is valid."""

    if "Sneaky" in attacking_card.keywords and "Sneaky" not in blocking_card.keywords:
        return False # Sneaky can only be blocked by Sneaky
    # Add other blocking rules if they exist (e.g., cards that cannot block)
    return True

def get_card_by_uuid(game_state: GameState, card_uuid: UUID) -> Card:
    """Returns a card by its UUID from the game state."""
    for player in [game_state.get_active_player(), game_state.get_inactive_player()]:
        for card in player.play_area + player.hand + player.discard_pile:
            if card.uuid == card_uuid:
                return card
    else:
        raise ValueError(f"Card with UUID {card_uuid} not found in game state.")

def get_effective_power(game_state: GameState, card_uuid: UUID) -> int:
    """Returns the effective power of a card, considering any passive effects."""
    card = get_card_by_uuid(game_state, card_uuid)
    effective_power = card.power

    for other_card in game_state.get_active_player().play_area + game_state.get_inactive_player().play_area:
        if other_card.ability_type == "passive":
            handler = passive_ability_handlers.get(other_card.id)
            if handler:
                effective_power += handler(game_state, other_card.uuid, card.uuid)
    
    return effective_power
    