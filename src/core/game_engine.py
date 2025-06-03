from typing import Dict, List, Optional
import copy
from src.models.game_state import GameState
from src.models.action import (
    Action, PlayCardAction, AttackAction,
    UseMindbugAction, PassMindbugAction,
    CardChoiceRequest
)
from src.models.card import Card
import src.core.game_rules as GameRules
from src.agents.base_agent import BaseAgent

class GameEngine:
    def __init__(self, deck_size: int = 10, hand_size: int = 5, agents: Dict[str, BaseAgent] = {}):
        self.deck_size = deck_size
        self.hand_size = hand_size
        self.agents = agents

    def apply_action(self, game_state: GameState, action: Action) -> GameState:
        """
        Applies a player's action to the current game state and returns the new state.
        This is the core method for advancing the game.
        """
        if game_state.game_over:
            print("Game is already over. Cannot apply more actions.")
            return game_state

        new_state = copy.deepcopy(game_state)

        if new_state.phase == "mindbug_phase":
            # Handle Mindbug response actions (UseMindbugAction, PassMindbugAction)
            return self._handle_mindbug_response(new_state, action)
        
        # Normal turn actions
        if action.player_id != new_state.active_player_id:
            print(f"Invalid action: It's not {action.player_id}'s turn.")
            return new_state # Or raise an error

        if isinstance(action, PlayCardAction):
            return self._handle_play_card_action(new_state, action)
        elif isinstance(action, AttackAction):
            return self._handle_attack_action(new_state, action)
        else:
            print(f"Unknown or invalid action type: {type(action)}")
            return new_state
    
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

    # --- Action Handlers (private methods within GameEngine) ---

    def _handle_play_card_action(self, game_state: GameState, action: PlayCardAction) -> GameState:
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()
        card_to_play_uuid = action.card_uuid

        for card in player.hand:
            if card.uuid == card_to_play_uuid:
                card_to_play = card
                break
        else:
            print(f"Error: Card UUID '{card_to_play_uuid}' not found in {player.id}'s hand.")
            return game_state # Invalid action, return original state
            
        # 1. Remove card from hand
        player.play_card(card_to_play) # player.play_card removes it from hand and adds it to play_area.
        print(f"{player.id} plays {card_to_play.name}.")

        # 2. Draw back to hand_size cards (Mindbug rule)
        while len(player.hand) < self.hand_size and player.deck:
            drawn_card = player.draw_card()
        
        # 3. Opponent gets a chance to Mindbug (Crucial Mindbug mechanic!)
        game_state._pending_mindbug_card_uuid = card_to_play.uuid # Store the card being played for Mindbug decision
        game_state.phase = "mindbug_phase" # Set phase to mindbug
        game_state.switch_active_player() # Switch to opponent for Mindbug decision
        # Store the card being played temporarily for Mindbug decision
        
        print(f"{opponent.id}, do you want to Mindbug {card_to_play.name}?")
        # The game loop will now wait for a UseMindbugAction or PassMindbugAction from inactive player.
        
        return game_state # State is now waiting for Mindbug response

    def _handle_mindbug_response(self, game_state: GameState, action: Action) -> GameState:
        opponent = game_state.get_active_player() # In mindbug phase, the "active" player is the opponent.
        player = game_state.get_inactive_player() # The player who originally played the card.
        # Get the card pending Mindbug response
        played_card = None
        for card in player.play_area:
            if card.uuid == game_state._pending_mindbug_card_uuid:
                played_card = card
                break
        else:
            print(f"Invalid Mindbug response: No played card found for UUID {game_state._pending_mindbug_card_uuid}.")
            return game_state

        if action.player_id != opponent.id:
            print(f"Invalid Mindbug response: Not {opponent.id}'s turn to respond.")
            return game_state
        
        if isinstance(action, UseMindbugAction):
            if opponent.mindbugs:
                opponent.use_mindbug()
                print(f"{opponent.id} uses a Mindbug on {played_card.name}!")

                # 1. Add played card to opponent's battlefield
                opponent.play_area.append(played_card)
                played_card.controller = opponent # Update controller
                # 2. Remove played card from original player's hand
                player.play_area.remove(played_card)
                # 3. Activate the card's play ability for the opponent
                game_state = GameRules.activate_play_ability(game_state, played_card.uuid, self.agents)
                # Now we do NOT switch back to the original player, so that when the turn ends they go again.
                
            else:
                print(f"{opponent.id} tried to Mindbug but has no Mindbugs left.")
                # Fall through to act as if they passed
                game_state.switch_active_player() # Switch back to original player
                game_state = GameRules.activate_play_ability(game_state, played_card.uuid, self.agents)

        elif isinstance(action, PassMindbugAction):
            print(f"{opponent.id} passes on Mindbugging {played_card.name}.")
            game_state.switch_active_player() # Switch back to original player
            game_state = GameRules.activate_play_ability(game_state, played_card.uuid, self.agents)

        game_state._pending_mindbug_card_uuid = None # Clear pending Mindbug state
        game_state = self.end_turn(game_state) # End turn after Mindbug resolution
        return game_state

    def _handle_attack_action(self, game_state: GameState, action: AttackAction) -> GameState:
        attacking_player = game_state.get_active_player()
        blocking_player = game_state.get_inactive_player()
        attacking_card = GameRules.get_card_by_uuid(game_state, action.attacking_card_uuid)
        if attacking_card not in attacking_player.play_area:
            raise ValueError(f"Attacking card {attacking_card.name} not found in {attacking_player.id}'s play area.")

        print(f"{attacking_player.id}'s {attacking_card.name} attacks!")

        # Activate "Attack" abilities (e.g., Tusked Extorter)
        game_state = GameRules.activate_attack_ability(game_state, attacking_card.uuid, self.agents)

        blocking_card: Optional[Card] = None

        # Activate "Hunter" keyword
        if "Hunter" in GameRules.get_effective_keywords(game_state, attacking_card.uuid):
            # Create a choice request
            choice_request = CardChoiceRequest(
                player_id=attacking_player.id,
                options=blocking_player.play_area,
                min_choices=0,
                max_choices=min(1, len(blocking_player.play_area)),
                purpose="hunt",
                prompt=f"{attacking_player.id}, HUNT an enemy creature that will block the attack (or none)."
            )
            # Ask the agent to choose
            agent = self.agents[attacking_player.id]
            blocker_list = agent.choose_cards(game_state, choice_request)
            if blocker_list:
                blocking_card = blocker_list[0] 

        # If no Hunter ability or no blocker was chosen, check if opponent has a blocker
        if not blocking_card:
            valid_blockers = []
            for card in blocking_player.play_area:
                if GameRules.is_valid_blocker(
                    blocking_card_uuid=card.uuid, 
                    attacking_card_uuid=attacking_card.uuid, 
                    game_state=game_state,
                ):
                    valid_blockers.append(card)
            
            # if not valid_blockers:
            #     # No blockers available, opponent takes damage
            #     print(f"{blocking_player.id} has no valid blockers. {attacking_player.id} deals damage directly!")
            #     game_state = self.lose_life(game_state, blocking_player.id)
            #     game_state = self.end_turn(game_state)  # End turn after attack resolution
            #     return game_state
            if valid_blockers:
                # Opponent has blockers, so they can choose one
                # Store the attacking card in the game state
                game_state._pending_attack_card_uuid = attacking_card.uuid 
                # Create a choice request
                choice_request = CardChoiceRequest(
                    player_id=blocking_player.id,
                    options=valid_blockers,
                    min_choices=0,
                    max_choices=1,
                    purpose="block",
                    prompt=f"{blocking_player.id}, choose a creature that will BLOCK the attack."
                )
                # Ask the agent to choose
                agent = self.agents[blocking_player.id]
                blocker_list = agent.choose_cards(game_state, choice_request)
                if blocker_list:
                    blocking_card = blocker_list[0] 
                # Reset the pending attack card
                del game_state._pending_attack_card_uuid

        if not blocking_card:
            # No blocker was chosen, opponent takes damage
            print(f"{blocking_player.id} does not block. {attacking_player.id} deals damage directly!")
            game_state = self.lose_life(game_state, blocking_player.id)
        else:
            print(f"{blocking_card.name} and {attacking_card.name} face each other.")
            # Resolve combat
            game_state = GameRules.resolve_combat(game_state, attacking_card.uuid, blocking_card.uuid, self.agents)

        # Handle "Frenzy" keyword
        attacking_player = game_state.get_player(attacking_player.id) # Refresh player state after combat resolution
        attacking_card = GameRules.get_card_by_uuid(game_state, action.attacking_card_uuid)
        if ("Frenzy" in GameRules.get_effective_keywords(game_state, attacking_card.uuid) 
            and not game_state._frenzy_active # Ensure Frenzy has not already been activated
            and attacking_card in attacking_player.play_area # Ensure the card has not been defeated
        ):
            # If the attacking card has Frenzy, it can choose to attack again immediately
            choice_request = CardChoiceRequest(
                player_id=attacking_player.id,
                options=[attacking_card],
                min_choices=0,
                max_choices=1,
                purpose="attack_again",
                prompt=f"{attacking_card.name} has Frenzy! Do you want to attack again?"
            )
            agent = self.agents[attacking_player.id]
            attack_again = agent.choose_cards(game_state, choice_request)
            if attack_again:
                print(f"{attacking_player.id} chooses to attack again with {attacking_card.name}!")
                game_state._frenzy_active = True # Set Frenzy state to active
                game_state = self._handle_attack_action(game_state, action) # Recursively handle the attack again
                game_state._frenzy_active = False # Reset Frenzy state
        
        if not game_state._frenzy_active:
            game_state = self.end_turn(game_state)
        return game_state

    def end_turn(self, game_state: GameState) -> GameState:
        # Check if game is over before ending turn
        if game_state.is_game_over():
            return game_state
        
        print(f"Turn {game_state.turn_count} ended.\n")
        game_state.switch_active_player() # Switch active player
        game_state.turn_count += 1 # Increment turn count
        game_state.phase = "play_phase"

        return game_state

    # --- Check of possible actions ---

    def get_valid_actions(self, game_state: GameState) -> List[Dict[str, Action | str]]:
        """
        Determines all legal actions the active player can take in the current game state.
        This is critical for AI and human input validation.
        """
        valid_actions: List[Dict[str, Action | str]] = []
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()

        if game_state.game_over:
            return []

        if game_state.phase == "mindbug_phase":
            # During the mindbug phase, the active player must choose whether to use a mindbug or not.
            if active_player.mindbugs:
                if game_state._pending_mindbug_card_uuid:
                    # If there is a pending Mindbug card, the player can choose to use a Mindbug on it.
                    card_name = GameRules.get_card_by_uuid(game_state, game_state._pending_mindbug_card_uuid).name
                else:
                    raise ValueError("Mindbug phase entered without a pending Mindbug card.")
                valid_actions.append({'action': UseMindbugAction(active_player.id),
                                      'card_name': card_name})
            valid_actions.append({'action': PassMindbugAction(active_player.id)})
            return valid_actions

        elif game_state.phase == "play_phase":
            # During the play phase, the active player can play a card or attack with a card on the play area.
            for card in active_player.hand:
                valid_actions.append({'action': PlayCardAction(active_player.id, card.uuid),
                                      'card_name': card.name})
            for card in active_player.play_area:
                valid_actions.append({'action': AttackAction(active_player.id, card.uuid),
                                      'card_name': card.name})
            
        elif game_state.phase == "end_turn_phase":
            raise ValueError("Invalid game phase: end_turn_phase. This should not be directly queried for actions.")

        # General rule: a player must take an action. If they cannot, they lose.
        if not valid_actions and not game_state.game_over:
            print(f"No valid actions for {active_player.id}. They lose by inability to act.")
            game_state.game_over = True
            game_state.winner_id = inactive_player.id # Opponent wins
            return [] # No valid actions

        return valid_actions