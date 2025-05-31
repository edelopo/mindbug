from typing import Dict, List, Optional, Tuple
import copy
from src.models.game_state import GameState
from src.models.action import (
    Action, PlayCardAction, AttackAction,
    UseMindbugAction, PassMindbugAction, BlockAction
)
from src.models.card import Card
import src.core.game_rules as GameRules

class GameEngine:
    def __init__(self, deck_size: int = 10, hand_size: int = 5):
        self.deck_size = deck_size
        self.hand_size = hand_size

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
        elif isinstance(action, BlockAction):
            return self._handle_block_action(new_state, action)
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
                game_state = GameRules.activate_play_ability(game_state, played_card.uuid)
                # Now we do NOT switch back to the original player, so that when the turn ends they go again.
                
            else:
                print(f"{opponent.id} tried to Mindbug but has no Mindbugs left.")
                # Fall through to act as if they passed
                game_state.switch_active_player() # Switch back to original player
                game_state = GameRules.activate_play_ability(game_state, played_card.uuid)

        elif isinstance(action, PassMindbugAction):
            print(f"{opponent.id} passes on Mindbugging {played_card.name}.")
            game_state.switch_active_player() # Switch back to original player
            game_state = GameRules.activate_play_ability(game_state, played_card.uuid)

        game_state._pending_mindbug_card_uuid = None # Clear pending Mindbug state
        game_state = self.end_turn(game_state) # End turn after Mindbug resolution
        return game_state

    def _handle_attack_action(self, game_state: GameState, action: AttackAction) -> GameState:
        attacking_player = game_state.get_active_player()
        blocking_player = game_state.get_inactive_player()
        attacking_card_uuid = action.attacking_card_uuid

        for card in attacking_player.play_area:
            if card.uuid == attacking_card_uuid:
                attacking_card = card
                break
        else:
            print(f"Error: Card UUID '{attacking_card_uuid}' not found in {attacking_player.id}'s play area.")
            return game_state # Invalid action, return original state

        print(f"{attacking_player.id}'s {attacking_card.name} attacks!")

        # Activate "Attack" abilities (e.g., Tusked Extorter)
        game_state = GameRules.activate_attack_ability(game_state, attacking_card.uuid)

        # Check if opponent has a blocker
        exist_valid_blockers = False
        for card in blocking_player.play_area:
            if GameRules.is_valid_blocker(
                blocking_card=card, attacking_card=attacking_card, 
                blocking_player_play_area=blocking_player.play_area, attacking_player_play_area=attacking_player.play_area
            ):
                exist_valid_blockers = True
                break
        
        if not exist_valid_blockers:
            # No blockers available, opponent takes damage
            print(f"{blocking_player.id} has no valid blockers. {attacking_player.id} deals damage directly!")
            game_state = self.lose_life(game_state, blocking_player.id)
            game_state = self.end_turn(game_state)  # End turn after attack resolution
            return game_state
        else:
            # Opponent has blockers, transition to block phase
            print(f"{blocking_player.id} has valid blockers. Transitioning to block phase.")
            game_state.phase = "block_phase"
            game_state._pending_attack_card_uuid = attacking_card.uuid  # Store the attacking card for block decision
            game_state.switch_active_player()
            return game_state  # Now waiting for BlockAction from opponent

    def _handle_block_action(self, game_state: GameState, action: BlockAction) -> GameState:
        blocking_player = game_state.get_active_player() # Opponent is active during block phase
        attacking_player = game_state.get_inactive_player() # The player who attacked

        attacking_card: Optional[Card] = None
        for card in attacking_player.play_area:
            if card.uuid == game_state._pending_attack_card_uuid:
                attacking_card = card
                break
        else:
            raise ValueError(f"Attacking card UUID '{game_state._pending_attack_card_uuid}' not found in {attacking_player.id}'s play area.")

        if action.blocking_card_uuid:
            # Opponent chose to block
            blocking_card: Optional[Card] = None
            for card in blocking_player.play_area:
                if card.uuid == action.blocking_card_uuid:
                    blocking_card = card
                    break
            else:
                print(f"Error: Blocking card UUID '{action.blocking_card_uuid}' not found in {blocking_player.id}'s play area.")
                return game_state
            
            is_valid_blocker = GameRules.is_valid_blocker(
                attacking_card=attacking_card, blocking_card=blocking_card,
                blocking_player_play_area=blocking_player.play_area,
                attacking_player_play_area=attacking_player.play_area
            )
            if not is_valid_blocker:
                print(f"Error: {attacking_card.name} is not a valid blocker.")
                return game_state

            print(f"{blocking_player.id}'s {blocking_card.name} blocks {attacking_card.name}.")
            
            # Resolve combat
            game_state, defeated_cards_uuid = GameRules.resolve_combat(game_state, attacking_card.uuid, blocking_card.uuid)

            # Activate "Defeated" abilities
            # TODO: Implement phase to choose the order of defeated abilities if there are multiple
            for defeated_card_uuid in defeated_cards_uuid:
                game_state = GameRules.activate_defeated_ability(game_state, defeated_card_uuid)
        else:
            # Opponent chose not to block
            print(f"{blocking_player.id} chooses not to block.")
            game_state = self.lose_life(game_state, blocking_player.id)

        del game_state._pending_attack_card_uuid  # Clear pending attack state
        game_state.switch_active_player()  # Switch back to attacking player to get the correct game state
        game_state = self.end_turn(game_state)  # End turn after block resolution

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

        elif game_state.phase == "block_phase":
            # During the block phase, the active player is the opponent
            valid_actions.append({'action': BlockAction(active_player.id, None),
                                  'card_name': "None"})  # Option to not block
            attacking_card_uuid = game_state._pending_attack_card_uuid
            if attacking_card_uuid:
                attacking_card = GameRules.get_card_by_uuid(game_state, attacking_card_uuid)
                for card in active_player.play_area:
                    # Check if the card can block the pending attack
                    if GameRules.is_valid_blocker(card, attacking_card,
                                                        active_player.play_area, inactive_player.play_area):
                        valid_actions.append({'action': BlockAction(active_player.id, card.uuid),
                                              'card_name': card.name})
            else:
                # Should not happen in "block_phase"
                raise ValueError("Block phase entered without a pending attack card.")
            
        elif game_state.phase == "end_turn_phase":
            raise ValueError("Invalid game phase: end_turn_phase. This should not be directly queried for actions.")

        # General rule: a player must take an action. If they cannot, they lose.
        if not valid_actions and not game_state.game_over:
            print(f"No valid actions for {active_player.id}. They lose by inability to act.")
            game_state.game_over = True
            game_state.winner_id = inactive_player.id # Opponent wins
            return [] # No valid actions

        return valid_actions