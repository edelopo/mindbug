from typing import Dict, List, Optional, Tuple
import copy
from src.models.game_state import GameState
from src.models.action import (
    Action, PlayCardAction, AttackAction,
    UseMindbugAction, PassMindbugAction, BlockAction
)
from src.models.card import Card
from src.core.game_rules import GameRules

class GameEngine:
    def __init__(self, card_definitions: Dict[str, Card], deck_size: int = 10, hand_size: int = 5):
        self.game_rules = GameRules(card_definitions, deck_size, hand_size)

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

    # --- Action Handlers (private methods within GameEngine) ---

    def _handle_play_card_action(self, game_state: GameState, action: PlayCardAction) -> GameState:
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()
        card_to_play_uuid = action.card.uuid

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
        while len(player.hand) < self.game_rules.hand_size and player.deck:
            drawn_card = player.draw_card()
            print(f"{player.id} draws {drawn_card.name} to refill hand.")
        
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
                game_state = self.game_rules.activate_play_ability(game_state, played_card, opponent.id)
                # Now we do NOT switch back to the original player, so that when the turn ends they go again.
                
            else:
                print(f"{opponent.id} tried to Mindbug but has no Mindbugs left.")
                # Fall through to act as if they passed
                game_state.switch_active_player() # Switch back to original player
                game_state = self.game_rules.activate_play_ability(game_state, played_card, game_state.active_player_id)

        elif isinstance(action, PassMindbugAction):
            print(f"{opponent.id} passes on Mindbugging {played_card.name}.")
            game_state.switch_active_player() # Switch back to original player
            game_state = self.game_rules.activate_play_ability(game_state, played_card, game_state.active_player_id)

        game_state._pending_mindbug_card_uuid = None # Clear pending Mindbug state
        game_state = self.end_turn(game_state) # End turn after Mindbug resolution
        return game_state

    def _handle_attack_action(self, game_state: GameState, action: AttackAction) -> GameState:
        attacker = game_state.get_active_player()
        blocker = game_state.get_inactive_player()
        attacking_card_uuid = action.attacking_card.uuid

        for card in attacker.play_area:
            if card.uuid == attacking_card_uuid:
                attacking_card = card
                break
        else:
            print(f"Error: Card UUID '{attacking_card_uuid}' not found in {attacker.id}'s play area.")
            return game_state # Invalid action, return original state
        # attacking_card = action.attacking_card

        print(f"{attacker.id}'s {attacking_card.name} attacks!")

        # Activate "Attack" abilities (e.g., Tusked Extorter)
        game_state = self.game_rules.activate_attack_ability(game_state, attacking_card)

        # Check if opponent has a blocker
        exist_valid_blockers = False
        for card in blocker.play_area:
            if self.game_rules.is_card_valid_blocker(
                blocking_card=card, attacking_card=attacking_card, 
                blocker_play_area=blocker.play_area, attacker_play_area=attacker.play_area
            ):
                exist_valid_blockers = True
                break
        
        if not exist_valid_blockers:
            # No blockers available, opponent takes damage
            print(f"{blocker.id} has no valid blockers. {attacker.id} deals damage directly!")
            game_state = self.game_rules.lose_life(game_state, blocker.id)
            game_state = self.end_turn(game_state)  # End turn after attack resolution
            return game_state
        else:
            # Opponent has blockers, transition to block phase
            print(f"{blocker.id} has valid blockers. Transitioning to block phase.")
            game_state.phase = "block_phase"
            game_state._pending_attack_card_uuid = attacking_card

        # --- IMPORTANT ---
        # Here, the GameEngine needs to *ask* the opponent's agent for a BlockAction.
        # This implies a mini-turn for the opponent.
        # For a simple text-based game, you'd prompt the opponent.
        # For AI, the opponent's agent would `choose_action(game_state)` with current phase being "block_phase".

        # For now, let's simplify and immediately resolve by checking action.target_id.
        # In a real engine, `apply_action` would check the phase and delegate.
        # Let's assume `AttackAction` has a `blocker_id` or `target_player_id`
        # for now.
        
        # The `AttackAction` should ideally *not* contain the blocker choice.
        # Instead, the `GameEngine` transitions to a "block_phase" and expects a `BlockAction`.

        # Let's update `AttackAction` and `BlockAction` to reflect this phase
        # Action: Attacker chooses target (player or card)
        # Then, if target is card, or if target is player and opponent has blockers,
        # opponent gets to choose a blocker.
        
        # Let's assume for this example, the AttackAction implies either attacking player or card.
        # If `action.target_id` is a player ID, it's a direct attack.
        # If `action.target_id` is a card ID, it's an attack on that card.

        target_card: Optional[Card] = None
        for card in opponent_cards:
            if card.id == action.target_id:
                target_card = card
                break

        if target_card:
            # Attacking a card directly (Mindbug doesn't work this way, usually)
            # In Mindbug, you declare attack, opponent *chooses* to block or take life.
            # So `AttackAction` should only specify attacker, not target.
            # The GameEngine then asks for a `BlockAction`.

            # REVISED FLOW for Attack:
            # 1. Player declares `AttackAction(player_id, attacking_card_id)`
            # 2. GameEngine processes this, sets `game_state.phase = "block_phase"`
            #    and stores `game_state._pending_attack_card = attacking_card`.
            # 3. GameEngine then expects `BlockAction` from inactive player.
            
            print(f"Error: Mindbug attack logic implies player declares attack, opponent chooses block/life. "
                  f"AttackAction target should not be a card directly.")
            return game_state # This branch indicates a misunderstanding of Mindbug attack rules.
        
        else: # Attacking opponent directly
            print(f"{player.id}'s {attacking_card.name} attacks {opponent.id} directly!")
            
            # Opponent decides to block or take life.
            # This is where the game engine would prompt the opponent's agent.
            # For now, let's assume if `target_id` is opponent_id, they *always* take life if they can't block.
            # Or, for simplicity for now, they take a life if no blocker was provided.
            
            # This state needs to be set up to receive a BlockAction.
            game_state.phase = "block_phase"
            game_state._pending_attack_card = attacking_card # Store for block decision
            game_state._current_attacker_player_id = player.id # Who is attacking
            print(f"Waiting for {opponent.id} to choose a blocker or take life.")
            return game_state # State is now waiting for block action

    # def _handle_block_action(self, game_state: GameState, action: BlockAction) -> GameState:
    #     opponent = game_state.get_active_player() # Opponent is active during block phase
    #     active_player = game_state.get_inactive_player() # The player who attacked

    #     attacking_card = game_state._pending_attack_card
    #     if not attacking_card or attacking_card.id != action.attacking_card_id:
    #         print("Error: No pending attack card or ID mismatch for block action.")
    #         return game_state

    #     if action.blocking_card_id:
    #         # Opponent chose to block
    #         blocking_card: Optional[Card] = None
    #         for card in game_state.battlefield[opponent.id]:
    #             if card.id == action.blocking_card_id:
    #                 blocking_card = card
    #                 break
            
    #         if not blocking_card or not self.game_rules.is_card_valid_blocker(attacking_card, blocking_card):
    #             print(f"Error: Invalid blocking card or not a valid blocker for {attacking_card.name}.")
    #             return game_state

    #         print(f"{opponent.id}'s {blocking_card.name} blocks {attacking_card.name}.")
            
    #         # Resolve combat
    #         game_state, (defeated_attackers_ids, defeated_blockers_ids) = \
    #             self.game_rules.resolve_combat(game_state, attacking_card, blocking_card)

    #         # Update battlefield and discard pile
    #         # This needs to find the Card objects by ID and move them.
    #         # For simplicity, this part will be a bit verbose:
            
    #         # Remove defeated from attacker's battlefield
    #         game_state.battlefield[active_player.id] = [
    #             c for c in game_state.battlefield[active_player.id] if c.id not in defeated_attackers_ids
    #         ]
    #         for defeated_id in defeated_attackers_ids:
    #             # Find the actual card object to move to discard
    #             for c in game_state.battlefield[active_player.id]: # Re-search for the card if it wasn't removed
    #                 if c.id == defeated_id:
    #                     active_player.discard_pile.append(c.card) # Move the base Card to discard
    #                     print(f"{c.name} (from {active_player.id}) was defeated and discarded.")
    #                     break # Found and processed
            
    #         # Remove defeated from blocker's battlefield
    #         game_state.battlefield[opponent.id] = [
    #             c for c in game_state.battlefield[opponent.id] if c.id not in defeated_blockers_ids
    #         ]
    #         for defeated_id in defeated_blockers_ids:
    #             # Find the actual card object to move to discard
    #             for c in game_state.battlefield[opponent.id]: # Re-search for the card if it wasn't removed
    #                 if c.id == defeated_id:
    #                     opponent.discard_pile.append(c.card) # Move the base Card to discard
    #                     print(f"{c.name} (from {opponent.id}) was defeated and discarded.")
    #                     break # Found and processed

    #     else:
    #         # Opponent chose not to block (or couldn't)
    #         print(f"{opponent.id} chooses not to block.")
    #         game_state = self.game_rules.lose_life(game_state, opponent.id, 1)

    #     # Clean up pending attack state
    #     del game_state._pending_attack_card
    #     del game_state._current_attacker_player_id
    #     game_state.phase = "attack_resolution_phase" # Or just "main_phase" if player can attack again

    #     return game_state

    def end_turn(self, game_state: GameState) -> GameState:
        # Check if game is over before ending turn
        if game_state.is_game_over():
            return game_state
        
        print(f"Turn {game_state.turn_count} ended.\n")
        game_state.switch_active_player() # Switch active player
        game_state.turn_count += 1 # Increment turn count
        print(f"Turn {game_state.turn_count}: {game_state.active_player_id} to play or attack.")
        print("Current state of the game:")
        for player_id, player in game_state.players.items():
            print(f"{player_id}'s play area: {[c.name for c in player.play_area]}\n"
                  f"{player.life_points} life points, {player.mindbugs} mindbugs.")
        game_state.phase = "play_phase"

        return game_state

    # def get_valid_actions(self, game_state: GameState) -> List[Action]:
    #     """
    #     Determines all legal actions the active player can take in the current game state.
    #     This is critical for AI and human input validation.
    #     """
    #     valid_actions: List[Action] = []
    #     active_player = game_state.get_active_player()
    #     inactive_player = game_state.get_inactive_player()

    #     if game_state.game_over:
    #         return []

    #     if self.mindbug_phase_active:
    #         # If in Mindbug response phase, only Mindbug-related actions are valid for the opponent
    #         played_card_id = game_state._pending_mindbug_card.id
    #         if opponent.mindbugs:
    #             valid_actions.append(UseMindbugAction(inactive_player.id, played_card_id))
    #         valid_actions.append(PassMindbugAction(inactive_player.id))
    #         return valid_actions

    #     # Normal turn actions based on phase
    #     if game_state.phase == "draw_phase":
    #         # Player automatically draws. No action needed from player, engine handles this.
    #         # Immediately transition to play phase.
    #         # This method should probably not be called during auto-draw.
    #         # For simplicity, if called, suggest to end turn or play.
    #         valid_actions.append(EndTurnAction(active_player.id)) # Still an option
    #         for card in active_player.hand:
    #             valid_actions.append(PlayCardAction(active_player.id, card.id))

    #     elif game_state.phase == "play_phase":
    #         # Can play a card or end turn
    #         for card in active_player.hand:
    #             valid_actions.append(PlayCardAction(active_player.id, card.id))
    #         valid_actions.append(EndTurnAction(active_player.id))

    #     elif game_state.phase == "attack_phase":
    #         # Can attack with an unexhausted card, or end turn
    #         for card in game_state.battlefield[active_player.id]:
    #             if not card.is_exhausted:
    #                 # Can attack player directly (if no blockers are forced)
    #                 valid_actions.append(AttackAction(active_player.id, card.id, inactive_player.id))
    #                 # Or attack specific cards if Hunter allows, or if it's a direct target
    #                 # (Mindbug doesn't generally allow targeting opponent's cards directly like this for attacks)
    #         valid_actions.append(EndTurnAction(active_player.id))

    #     elif game_state.phase == "block_phase":
    #         # Opponent is making a blocking decision
    #         attacking_card = game_state._pending_attack_card
    #         if attacking_card:
    #             # Option to not block
    #             valid_actions.append(BlockAction(inactive_player.id, attacking_card.id, None))
                
    #             # Options to block with valid cards
    #             for blocker in game_state.battlefield[inactive_player.id]:
    #                 if self.game_rules.is_card_valid_blocker(attacking_card, blocker):
    #                     valid_actions.append(BlockAction(inactive_player.id, attacking_card.id, blocker.id))
    #         else:
    #             # Should not happen in "block_phase"
    #             print("Warning: block_phase entered without pending attack.")
            
    #     elif game_state.phase == "end_turn_phase":
    #         # Only option is to transition to next turn, which the engine does automatically
    #         # or the player signals it with an EndTurnAction if multiple actions allowed.
    #         valid_actions.append(EndTurnAction(active_player.id))


    #     # General rule: a player must take an action. If they cannot, they lose.
    #     if not valid_actions and not game_state.game_over:
    #         print(f"No valid actions for {active_player.id}. They lose by inability to act.")
    #         game_state.game_over = True
    #         game_state.winner_id = inactive_player.id # Opponent wins
    #         return [] # No valid actions

    #     return valid_actions