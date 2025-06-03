import random
import copy
from uuid import UUID
from typing import List, Tuple, Dict
from src.models.game_state import GameState
from src.models.card import Card
from src.models.action import CardChoiceRequest
from src.agents.base_agent import BaseAgent

# --- Core Game Logic Functions ---

def defeat(game_state: GameState, card_uuids: UUID | List[UUID], agents: Dict[str, BaseAgent] = {}) -> GameState:
    """
    Defeats a card or list of cards by moving it from play area to discard pile.
    It includes Tough keyword handling and activation of Defeated abilities.
    Returns the updated GameState.
    """
    if isinstance(card_uuids, UUID):
        card = get_card_by_uuid(game_state, card_uuids)
        if card.controller is None:
            raise ValueError("Card has no controller. Cannot defeat.")   

        # Apply Tough
        if "Tough" in get_effective_keywords(game_state, card.uuid) and not card.is_exhausted:
            print(f"{card.name} is Tough. It becomes exhausted instead of defeated.")
            card.is_exhausted = True
        else:
            # Remove defeated card from play area and move to controller's discard pile
            card.controller.discard_pile.append(card)
            card.controller.play_area.remove(card)
            card.is_exhausted = False  # Reset exhausted state
            game_state = activate_defeated_ability(game_state, card.uuid, agents)

    elif isinstance(card_uuids, list):
        defeated_cards = []
        for card_uuid in card_uuids:
            card = get_card_by_uuid(game_state, card_uuid)
            if card.controller is None:
                raise ValueError("Card has no controller. Cannot defeat.")
            
            # Apply Tough
            if "Tough" in get_effective_keywords(game_state, card.uuid) and not card.is_exhausted:
                print(f"{card.name} is Tough. It becomes exhausted instead of defeated.")
                card.is_exhausted = True
            else:
                # Remove defeated card from play area and move to controller's discard pile
                card.controller.discard_pile.append(card)
                card.controller.play_area.remove(card)
                card.is_exhausted = False  # Reset exhausted state
                defeated_cards.append(card)
        
        # Ask the active player to choose the order of defeated abilities
        if defeated_cards:
            defeated_cards_with_defeated_abilities = [
                card for card in defeated_cards if card.ability_type == "defeated"
            ]
            if len(defeated_cards_with_defeated_abilities) > 1:
                choice_request = CardChoiceRequest(
                    player_id=game_state.active_player_id,
                    options=defeated_cards_with_defeated_abilities,
                    min_choices=len(defeated_cards_with_defeated_abilities),
                    max_choices=len(defeated_cards_with_defeated_abilities),
                    purpose="defeat_order",
                    prompt="Choose the order of defeated abilities to activate."
                )
                agent = agents[game_state.active_player_id]
                defeated_cards_with_defeated_abilities = agent.choose_cards(game_state, choice_request)
            for card in defeated_cards_with_defeated_abilities:
                game_state = activate_defeated_ability(game_state, card.uuid, agents)
    return game_state

def resolve_combat(game_state: GameState, attacker_uuid: UUID, 
                    blocker_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """
    Resolves a combat between two cards.
    Returns the updated GameState.
    """
    attacker = get_card_by_uuid(game_state, attacker_uuid)
    blocker = get_card_by_uuid(game_state, blocker_uuid)
    if attacker.controller is None or blocker.controller is None:
        raise ValueError("Attacker or blocker has no controller. Cannot resolve combat.")
    
    effective_attacker_power = get_effective_power(game_state, attacker.uuid)
    effective_blocker_power = get_effective_power(game_state, blocker.uuid)

    print(f"Resolving combat: {attacker.name} (P={effective_attacker_power}) "
            f"vs {blocker.name} (P={effective_blocker_power})")

    defeated_cards_UUID: List[UUID] = []

    # Check for Poisonous keyword first
    if "Poisonous" in get_effective_keywords(game_state, attacker.uuid):
        print(f"{attacker.name} is Poisonous. {blocker.name} is defeated.")
        defeated_cards_UUID.append(blocker.uuid)
        
    if "Poisonous" in get_effective_keywords(game_state, blocker.uuid):
        print(f"{blocker.name} is Poisonous. {attacker.name} is defeated.")
        defeated_cards_UUID.append(attacker.uuid)

    # Effective power comparison
    if effective_attacker_power > effective_blocker_power:
        print(f"{attacker.name} defeats {blocker.name}.")
        defeated_cards_UUID.append(blocker.uuid)
    elif effective_blocker_power > effective_attacker_power:
        print(f"{blocker.name} defeats {attacker.name}.")
        defeated_cards_UUID.append(attacker.uuid)
    else: # Equal power
        print(f"{attacker.name} and {blocker.name} defeat each other.")
        defeated_cards_UUID.append(attacker.uuid)
        defeated_cards_UUID.append(blocker.uuid)

    defeated_cards_UUID = list(set(defeated_cards_UUID))  # Remove duplicates
    game_state = defeat(game_state, defeated_cards_UUID, agents) # This handles Choice of order of defeated abilities
    
    return game_state


# --- Ability Handlers (called by GameEngine when appropriate) ---

def activate_play_ability(game_state: GameState, card_played_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Activates a card's 'Play' ability."""
    card_played = get_card_by_uuid(game_state, card_played_uuid)
    if card_played.controller is None:
        raise ValueError(f"Card with UUID {card_played_uuid} has no controller. Cannot activate play ability.")
    opponent = game_state.get_opponent_of(card_played.controller.id)
    if "deathweaver" in [card.id for card in opponent.play_area]:
        print(f"{card_played.name} cannot activate its play ability because Deathweaver is in play.")
        return game_state
    if card_played.ability_type == "play":
        print(f"Activating Play ability of {card_played.name} for {card_played.controller.id}")
        handler = play_ability_handlers.get(card_played.id)
        if handler:
            game_state = handler(copy.deepcopy(game_state), card_played_uuid, agents)
    return game_state

def activate_attack_ability(game_state: GameState, attacking_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
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

def activate_defeated_ability(game_state: GameState, defeated_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
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

def _axolotl_healer_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Axolotl Healer's 'Play' effect: Gain 2 life points."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    player = card_played.controller
    if player is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")

    # Player gains 2 life
    player.life_points += 2
    print(f"{player.id} gains 2 life points. New life: {player.life_points}")

    return game_state

def _brain_fly_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Brain Fly's 'Play' effect: Take control of a creature with power 6 or more."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    player = card_played.controller
    opponent = game_state.get_opponent_of(player.id)

    valid_targets = []
    for card in opponent.play_area:
        effective_power = get_effective_power(game_state, card.uuid)
        if effective_power >= 6:
            valid_targets.append(card)

    if not valid_targets:
        print(f"No valid creatures with power 6 or more to take control of.")
        return game_state
    
    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=valid_targets,
        min_choices=1,
        max_choices=1,
        purpose="steal",
        prompt="Choose a creature with power 6 or more to STEAL."
    )

    # Ask the agent to choose
    agent = agents[player.id]
    chosen_card = agent.choose_cards(game_state, choice_request)[0]

    # Steal the chosen card
    opponent.play_area.remove(chosen_card)
    player.play_area.append(chosen_card)
    chosen_card.controller = player
    print(f"{player.id} steals {chosen_card.name} from {opponent.id}.")

    return game_state

def _compost_dragon_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Compost Dragon's 'Play' effect: Play a card from your discard pile."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    player = card_played.controller

    if not player.discard_pile:
        print(f"{player.id} has no cards in discard pile to play.")
        return game_state

    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=player.discard_pile,
        min_choices=1,
        max_choices=1,
        purpose="play",
        prompt="Choose a card from your discard pile to PLAY."
    )

    # Ask the agent to choose
    agent = agents[player.id]
    chosen_card = agent.choose_cards(game_state, choice_request)[0]

    # Move the chosen card from discard pile to play area
    player.discard_pile.remove(chosen_card)
    player.play_area.append(chosen_card)
    chosen_card.controller = player
    print(f"{player.id} plays {chosen_card.name} from their discard pile.")
    game_state = activate_play_ability(game_state, chosen_card.uuid, agents)

    return game_state

def _ferret_bomber_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Ferret Bomber's 'Play' effect: The opponent discards two cards."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    opponent = game_state.get_opponent_of(card_played.controller.id)

    if not opponent.hand:
        print(f"{opponent.id} has no cards in hand, cannot discard.")
        return game_state

    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=opponent.id,
        options=opponent.hand,
        min_choices=min(2, len(opponent.hand)),
        max_choices=min(2, len(opponent.hand)),
        purpose="discard",
        prompt="Choose two cards to DISCARD."
    )

    # Ask the agent to choose
    agent = agents[opponent.id]
    chosen_cards = agent.choose_cards(game_state, choice_request)

    for card in chosen_cards:
        opponent.discard_card(card)
        print(f"{opponent.id} discards {card.name} due to Ferret Bomber.")

    return game_state

def _giraffodile_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Giraffodile's 'Play' effect: Draw your entire discard pile."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    player = card_played.controller

    if not player.discard_pile:
        print(f"{player.id} has no cards in discard pile to draw.")
        return game_state

    # Move all cards from discard pile to hand
    for card in player.discard_pile[:]:  # Slice to avoid modifying while iterating
        player.hand.append(card)
        player.discard_pile.remove(card)
        card.controller = player  # Ensure the controller is set correctly
        print(f"{player.id} draws {card.name} from their discard pile.")

    return game_state

def _grave_robber_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Grave Robber's 'Play' effect: Play a card from the opponent's discard pile."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    player = card_played.controller
    opponent = game_state.get_opponent_of(player.id)

    if not opponent.discard_pile:
        print(f"{opponent.id} has no cards in discard pile to play.")
        return game_state

    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=opponent.discard_pile,
        min_choices=1,
        max_choices=1,
        purpose="play",
        prompt="Choose a card from the opponent's discard pile to PLAY."
    )

    # Ask the agent to choose
    agent = agents[player.id]
    chosen_card = agent.choose_cards(game_state, choice_request)[0]

    # Move the chosen card from opponent's discard pile to player's play area
    opponent.discard_pile.remove(chosen_card)
    player.play_area.append(chosen_card)
    chosen_card.controller = player
    print(f"{player.id} plays {chosen_card.name} from {opponent.id}'s discard pile.")
    game_state = activate_play_ability(game_state, chosen_card.uuid, agents)

    return game_state

def _kangasaurus_rex_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Kangasaurus Rex's 'Play' effect: Defeat all enemy creatures with power 4 or less.."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    opponent = game_state.get_opponent_of(card_played.controller.id)
    for card in opponent.play_area[:]: # We need to slice the list to avoid modifying it while iterating
        effective_power = get_effective_power(game_state, card.uuid)
        if effective_power <= 4:
            print(f"{card.name} (P={effective_power}) is defeated by Kangasaurus Rex.")
            game_state = defeat(game_state, card.uuid)
    return game_state

def _killer_bee_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Killer Bee's 'Play' effect: The opponent loses a life point."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    player = card_played.controller
    opponent = game_state.get_opponent_of(player.id)
    
    # Opponent loses 1 life
    opponent.life_points -= 1
    print(f"{opponent.id} loses 1 life point, now they have {opponent.life_points} left.")
    
    if opponent.life_points <= 0:
        game_state.game_over = True
        game_state.winner_id = player.id
        print(f"{opponent.id} has no life points left! {game_state.winner_id} wins!")

    return game_state

def _mysterious_mermaid_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Mysterious Mermaid's 'Play' effect: Set your life points equal to the opponent's."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    player = card_played.controller
    opponent = game_state.get_opponent_of(player.id)

    # Set player's life points to opponent's life points
    player.life_points = opponent.life_points
    print(f"{player.id}'s life points are now set to {player.life_points}.")

    return game_state

def _tiger_squirrel_play_ability(game_state: GameState, card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Tiger Squirrel's 'Play' effect: Defeat an enemy creature with power 7 or more."""
    card_played = get_card_by_uuid(game_state, card_uuid)
    if card_played.controller is None:
        raise ValueError("Card played has no controller. Cannot resolve play ability.")
    
    player = card_played.controller
    opponent = game_state.get_opponent_of(player.id)

    valid_targets = []
    for card in opponent.play_area:
        effective_power = get_effective_power(game_state, card.uuid)
        if effective_power >= 7:
            valid_targets.append(card)

    if not valid_targets:
        print(f"No valid creatures with power 7 or more to defeat.")
        return game_state
    
    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=valid_targets,
        min_choices=1,
        max_choices=1,
        purpose="defeat",
        prompt="Choose a creature with power 7 or more to DEFEAT."
    )

    # Ask the agent to choose
    agent = agents[player.id]
    chosen_card = agent.choose_cards(game_state, choice_request)[0]

    # Defeat the chosen card
    game_state = defeat(game_state, chosen_card.uuid, agents)
    
    return game_state

# -- Attack Abilities --

def _chameleon_sniper_attack_ability(game_state: GameState, attacking_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Chameleon Sniper's 'Attack' effect: The opponent loses a life point."""
    attacking_card = get_card_by_uuid(game_state, attacking_card_uuid)
    if attacking_card.controller is None:
        raise ValueError("Attacking card has no controller. Cannot resolve attack ability.")
    
    player = attacking_card.controller
    opponent = game_state.get_opponent_of(player.id)
    
    # Opponent loses 1 life
    opponent.life_points -= 1
    if opponent.life_points <= 0:
        game_state.game_over = True
        game_state.winner_id = player.id
        print(f"{opponent.id} has no life points left! {game_state.winner_id} wins!")

    return game_state

def _tusked_extorter_attack_ability(game_state: GameState, attacking_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Tusked Extorter's 'Attack' effect: The opponent discards a card."""
    attacking_card = get_card_by_uuid(game_state, attacking_card_uuid)
    if attacking_card.controller is None:
        raise ValueError("Attacking card has no controller. Cannot resolve attack ability.")
    
    opponent = game_state.get_opponent_of(attacking_card.controller.id)
    
    if not opponent.hand:
        print(f"{opponent.id}'s hand is empty, cannot discard.")
        return game_state

    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=opponent.id,
        options=opponent.hand,
        min_choices=1,
        max_choices=1,
        purpose="discard",
        prompt="Choose a card to DISCARD."
    )

    # Ask the agent to choose
    agent = agents[opponent.id]
    chosen_card = agent.choose_cards(game_state, choice_request)[0]
    opponent.discard_card(chosen_card)
    print(f"{opponent.id} discards {chosen_card.name} due to Tusked Extorter.")

    return game_state

def _shark_dog_attack_ability(game_state: GameState, attacking_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Shark Dog's 'Attack' effect: Defeat an enemy creature with power 6 or more."""
    attacking_card = get_card_by_uuid(game_state, attacking_card_uuid)
    if attacking_card.controller is None:
        raise ValueError("Attacking card has no controller. Cannot resolve attack ability.")
    
    player = attacking_card.controller
    opponent = game_state.get_opponent_of(player.id)

    valid_targets = []
    for card in opponent.play_area:
        effective_power = get_effective_power(game_state, card.uuid)
        if effective_power >= 6:
            valid_targets.append(card)

    if not valid_targets:
        print(f"No valid creatures with power 6 or more to defeat.")
        return game_state
    
    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=valid_targets,
        min_choices=1,
        max_choices=1,
        purpose="defeat",
        prompt="Choose a creature with power 6 or more to DEFEAT."
    )

    # Ask the agent to choose
    agent = agents[player.id]
    chosen_card = agent.choose_cards(game_state, choice_request)[0]

    # Defeat the chosen card
    game_state = defeat(game_state, chosen_card.uuid, agents)
    
    return game_state

def _snail_hydra_attack_ability(game_state: GameState, attacking_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Snail Hydra's 'Attack' effect: If you control fewer creatures than your opponent, defeat a creature."""
    attacking_card = get_card_by_uuid(game_state, attacking_card_uuid)
    if attacking_card.controller is None:
        raise ValueError("Attacking card has no controller. Cannot resolve attack ability.")
    
    player = attacking_card.controller
    opponent = game_state.get_opponent_of(player.id)

    # Check if player controls fewer creatures than opponent
    if len(player.play_area) < len(opponent.play_area):
        valid_targets = opponent.play_area + player.play_area  # Can defeat any creature

        if not valid_targets:
            print(f"No creatures to defeat.")
            return game_state
        
        # Create a choice request
        choice_request = CardChoiceRequest(
            player_id=player.id,
            options=valid_targets,
            min_choices=1,
            max_choices=1,
            purpose="defeat",
            prompt="Choose a creature to DEFEAT."
        )

        # Ask the agent to choose
        agent = agents[player.id]
        chosen_card = agent.choose_cards(game_state, choice_request)[0]

        # Defeat the chosen card
        game_state = defeat(game_state, chosen_card.uuid, agents)

    return game_state

# -- Defeated Abilities --

def _explosive_toad_defeated_ability(game_state: GameState, defeated_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Explosive Toad's 'Defeated' effect: Defeat a creature."""
    defeated_card = get_card_by_uuid(game_state, defeated_card_uuid)
    if defeated_card.controller is None:
        raise ValueError("Defeated card has no controller. Cannot resolve defeated ability.")
    
    player = defeated_card.controller
    opponent = game_state.get_opponent_of(player.id)

    valid_targets = opponent.play_area + player.play_area

    if not valid_targets:
        print(f"No creatures to defeat.")
        return game_state
    
    # Create a choice request
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=valid_targets,
        min_choices=min(1, len(valid_targets)),
        max_choices=1,
        purpose="defeat",
        prompt="Choose a creature to DEFEAT."
    )

    # Ask the agent to choose
    agent = agents[player.id]
    chosen_card = agent.choose_cards(game_state, choice_request)[0]

    # Defeat the chosen card
    game_state = defeat(game_state, chosen_card.uuid, agents)
    
    return game_state

def _harpy_mother_defeated_ability(game_state: GameState, defeated_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
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
    choice_request = CardChoiceRequest(
        player_id=player.id,
        options=valid_targets,
        min_choices=min(2, len(valid_targets)),
        max_choices=min(2, len(valid_targets)),
        purpose="steal",
        prompt="Choose up to two creatures with power 5 or less to STEAL."
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

def _strange_barrel_defeated_ability(game_state: GameState, defeated_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> GameState:
    """Strange Barrel's 'Defeated' effect: Steal two random cards from the opponent's hand."""
    defeated_card = get_card_by_uuid(game_state, defeated_card_uuid)
    if defeated_card.controller is None:
        raise ValueError("Defeated card has no controller. Cannot resolve defeated ability.")
    
    player = defeated_card.controller
    opponent = game_state.get_opponent_of(player.id)

    if not opponent.hand:
        print(f"{opponent.id} has no cards in hand to steal.")
        return game_state

    # Randomly select up to two cards from opponent's hand
    num_to_steal = min(2, len(opponent.hand))
    stolen_cards = random.sample(opponent.hand, num_to_steal)

    for card in stolen_cards:
        opponent.hand.remove(card)
        player.hand.append(card)
        card.controller = player
        print(f"{player.id} steals {card.name} from {opponent.id}'s hand.")

    return game_state

# -- Passive Abilities --
# Some of these are handled at the relevant part of the game logic, such as is_valid_blocker or resolve_combat.

def _goblin_werewolf_passive_ability(game_state: GameState, goblin_werewolf_uuid: UUID,
                                    affected_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> int:
    """Goblin Werewolf's 'Passive' effect: Has +6 power while it is your turn."""
    goblin_werewolf_controller = get_card_by_uuid(game_state, goblin_werewolf_uuid).controller
    if goblin_werewolf_controller:
        if (game_state.active_player_id == goblin_werewolf_controller.id
            and goblin_werewolf_uuid == affected_card_uuid):
            # Only apply the bonus if it's the controller's turn
            return 6
        else:
            return 0
    else:
        raise ValueError("Goblin Werewolf card has no controller. Cannot resolve passive ability.")

def _lone_yeti_passive_ability(game_state: GameState, lone_yeti_uuid: UUID,
                                affected_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> int:
    """Lone Yeti's 'Passive' effect: While this is your only allied creature, it has +5 power and Frenzy."""
    lone_yeti = get_card_by_uuid(game_state, lone_yeti_uuid)
    if lone_yeti.controller is None:
        raise ValueError("Lone Yeti card has no controller. Cannot resolve passive ability.")
    play_area = lone_yeti.controller.play_area
    if len(play_area) == 1 and play_area[0].uuid == lone_yeti_uuid and affected_card_uuid == lone_yeti_uuid:
        return 5
    return 0
    
def _shield_bugs_passive_ability(game_state: GameState, shield_bugs_uuid: UUID, 
                                    affected_card_uuid: UUID, agents: Dict[str, BaseAgent] = {}) -> int:
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


# --- Dicts of Ability Handlers ---

# Map card IDs to specific ability functions for "Play" effects
play_ability_handlers = {
    "axolotl_healer": _axolotl_healer_play_ability,
    "brain_fly": _brain_fly_play_ability,
    "compost_dragon": _compost_dragon_play_ability,
    "ferret_bomber": _ferret_bomber_play_ability,
    "giraffodile": _giraffodile_play_ability,
    "grave_robber": _grave_robber_play_ability,
    "kangasaurus_rex": _kangasaurus_rex_play_ability,
    "killer_bee": _killer_bee_play_ability,
    "mysterious_mermaid": _mysterious_mermaid_play_ability,
    "tiger_squirrel": _tiger_squirrel_play_ability,
}
# Map card IDs to specific ability functions for "Attack" effects
attack_ability_handlers = {
    "tusked_extorter": _tusked_extorter_attack_ability,
    "chameleon_sniper": _chameleon_sniper_attack_ability,
    "shark_dog": _shark_dog_attack_ability,
    "snail_hydra": _snail_hydra_attack_ability,
}
# Map card IDs to specific ability functions for "Defeated" effects
defeated_ability_handlers = {
    "explosive_toad": _explosive_toad_defeated_ability,
    "harpy_mother": _harpy_mother_defeated_ability,
    "strange_barrel": _strange_barrel_defeated_ability,
}
# Map card IDs to specific ability functions for "Passive" effects
passive_ability_handlers = {
    "goblin_werewolf": _goblin_werewolf_passive_ability,
    "lone_yeti": _lone_yeti_passive_ability,
    "shield_bugs": _shield_bugs_passive_ability,
}


# --- Utility methods for rules ---
# These might be used by GameEngine to determine valid actions or apply effects.

def is_valid_blocker(blocking_card_uuid: UUID, attacking_card_uuid: UUID,
                     game_state: GameState) -> bool:
    """Checks if a blocker is valid."""
    blocking_card = get_card_by_uuid(game_state, blocking_card_uuid)
    attacking_card = get_card_by_uuid(game_state, attacking_card_uuid)
    attacking_player = attacking_card.controller
    if attacking_player is None:
        raise ValueError("Attacking card has no controller. Cannot resolve blocking.")

    blocking_card_effective_power = get_effective_power(game_state, blocking_card.uuid)

    if ("Sneaky" in get_effective_keywords(game_state, attacking_card_uuid) 
        and "Sneaky" not in get_effective_keywords(game_state, blocking_card_uuid)):
        return False # Sneaky can only be blocked by Sneaky
    
    # Bee Bear ability
    if attacking_card.id == "bee_bear" and blocking_card_effective_power <= 6:
        return False
    
    # Elephantopus ability
    attacking_player_card_ids = [card.id for card in attacking_player.play_area]
    if "elephantopus" in attacking_player_card_ids and blocking_card_effective_power <= 4:
        return False
    
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
    
def get_effective_keywords(game_state: GameState, card_uuid: UUID) -> List[str]:
    """Returns the effective keywords of a card, considering any passive effects."""
    card = get_card_by_uuid(game_state, card_uuid)
    effective_keywords = set(card.keywords)

    player = card.controller
    if player is None:
        raise ValueError("Card has no controller. Cannot resolve effective keywords.")
    opponent = game_state.get_opponent_of(player.id)
    if opponent is None:
        raise ValueError("Opponent not found. Cannot resolve effective keywords.")

    # Lone Yeti passive ability
    if card.id == "lone_yeti" and len(player.play_area) == 1:
        effective_keywords.add("Frenzy")

    # Sharky Crab-Dog-Mummypus passive ability
    if card.id == "sharky_crab-dog-mummypus":
        for card in opponent.play_area:
            for keyword in card.keywords:
                if keyword in ["Hunter", "Sneaky", "Frenzy", "Poisonous"]:
                    effective_keywords.add(keyword)

    # Snail Thrower passive ability
    if "snail_thrower" in [other_card.id for other_card in player.play_area if other_card.uuid != card_uuid]:
        if get_effective_power(game_state, card.uuid) <= 4:
            effective_keywords.add("Hunter")
            effective_keywords.add("Poisonous")
    
    return list(effective_keywords)