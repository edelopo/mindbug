from typing import Dict, List, Optional, Tuple
from src.models.game_state import GameState
from src.models.action import (
    Action, PlayCreatureAction, AttackAction, EndTurnAction,
    UseMindbugAction, PassMindbugAction, BlockAction
)
from src.models.card import Card
from src.models.creature import Creature
from src.core.game_rules import GameRules # Import the GameRules class

class GameEngine:
    def __init__(self, card_definitions: Dict[str, Card]):
        self.game_rules = GameRules(card_definitions)
        self.mindbug_phase_active = False # Flag to manage Mindbug response

    def apply_action(self, game_state: GameState, action: Action) -> GameState:
        """
        Applies a player's action to the current game state and returns the new state.
        This is the core method for advancing the game.
        """
        if game_state.game_over:
            print("Game is already over. Cannot apply more actions.")
            return game_state

        new_state = game_state.copy() # Always work on a copy for AI robustness

        if self.mindbug_phase_active:
            # Handle Mindbug response actions (UseMindbugAction, PassMindbugAction)
            return self._handle_mindbug_response(new_state, action)
        
        # Normal turn actions
        if action.player_id != new_state.active_player_id:
            print(f"Invalid action: It's not {action.player_id}'s turn.")
            return new_state # Or raise an error

        if isinstance(action, PlayCreatureAction):
            return self._handle_play_creature_action(new_state, action)
        elif isinstance(action, AttackAction):
            return self._handle_attack_action(new_state, action)
        elif isinstance(action, EndTurnAction):
            return self._handle_end_turn_action(new_state, action)
        # elif isinstance(action, ActivateAbilityAction): # For later
        #     return self._handle_activate_ability_action(new_state, action)
        else:
            print(f"Unknown or invalid action type: {type(action)}")
            return new_state

    # --- Action Handlers (private methods within GameEngine) ---

    def _handle_play_creature_action(self, game_state: GameState, action: PlayCreatureAction) -> GameState:
        player = game_state.get_active_player()
        card_to_play = None

        # Find the card in hand
        for card in player.hand:
            if card.id == action.card_id:
                card_to_play = card
                break

        if not card_to_play:
            print(f"Error: Card '{action.card_id}' not found in {player.player_id}'s hand.")
            return game_state # Invalid action, return original state

        # 1. Remove card from hand
        player.play_card(card_to_play) # player.play_card removes it from hand
        print(f"{player.player_id} plays {card_to_play.name}.")

        # 2. Draw back to 5 cards (Mindbug rule)
        while len(player.hand) < 5 and player.deck:
            drawn_card = player.draw_card()
            print(f"{player.player_id} draws {drawn_card.name} to refill hand.")
        
        # 3. Opponent gets a chance to Mindbug (Crucial Mindbug mechanic!)
        self.mindbug_phase_active = True
        # Store the card being played temporarily for Mindbug decision
        game_state._pending_mindbug_card_for_opponent = card_to_play 
        
        print(f"{game_state.get_inactive_player().player_id}, do you want to Mindbug {card_to_play.name}?")
        # The game loop will now wait for a UseMindbugAction or PassMindbugAction from inactive player.
        
        return game_state # State is now waiting for Mindbug response

    def _handle_mindbug_response(self, game_state: GameState, action: Action) -> GameState:
        opponent = game_state.get_active_player() # In mindbug phase, the "active" player is the opponent.
        active_player_who_played = game_state.get_inactive_player() # The player who originally played the card.
        
        played_card = game_state._pending_mindbug_card_for_opponent
        if not played_card:
            print("Error: No card pending Mindbug response. This should not happen.")
            self.mindbug_phase_active = False # Reset flag
            return game_state

        if action.player_id != opponent.player_id:
            print(f"Invalid Mindbug response: Not {opponent.player_id}'s turn to respond.")
            return game_state
        
        if isinstance(action, UseMindbugAction):
            if action.played_card_id != played_card.id:
                 print(f"Error: Mindbug action target ({action.played_card_id}) does not match pending card ({played_card.id}).")
                 return game_state

            if opponent.mindbugs:
                mindbug_card = opponent.use_mindbug()
                print(f"{opponent.player_id} uses a Mindbug on {played_card.name}!")
                
                # Creature enters opponent's battlefield
                creature = Creature(played_card, opponent.player_id)
                game_state.battlefield[opponent.player_id].append(creature)
                creature.has_been_mindbugged = True # Mark it as mindbugged
                print(f"{creature.name} enters {opponent.player_id}'s battlefield.")

                # Activate Play ability for the *Mindbugging* player
                game_state = self.game_rules.activate_play_ability(game_state, creature, opponent.player_id)

                # Mindbugging player gets an extra turn (Mindbug rule)
                print(f"{opponent.player_id} gets an extra turn!")
                # To grant an extra turn, we need to swap active/inactive players,
                # but then *immediately* swap them back after this turn.
                # A simpler way is to just NOT swap players at the end of this current mini-turn.
                # For now, let's keep it simple: player who Mindbugged gets to act again
                # after this resolved mini-turn, the next action comes from them.
                # This requires careful phase management in the main loop.
                # A common solution is to have a "pending extra turn" flag.
                game_state._pending_extra_turn_for = opponent.player_id
                
            else:
                print(f"{opponent.player_id} tried to Mindbug but has no Mindbugs left.")
                # Fall through to act as if they passed
                return self._finalize_play_card_after_mindbug(game_state, played_card, active_player_who_played.player_id)

        elif isinstance(action, PassMindbugAction):
            print(f"{opponent.player_id} passes on Mindbugging {played_card.name}.")
            # Creature enters original player's battlefield
            return self._finalize_play_card_after_mindbug(game_state, played_card, active_player_who_played.player_id)

        self.mindbug_phase_active = False
        del game_state._pending_mindbug_card_for_opponent # Clean up
        return game_state

    def _finalize_play_card_after_mindbug(self, game_state: GameState, card_to_play: Card, original_player_id: str) -> GameState:
        """
        Places the creature on the battlefield and resolves its play effect if no Mindbug
        was used or if the Mindbug was used by the opponent.
        """
        # Determine the final controller of the creature
        # If Mindbug was used, the 'played_card' is already added to opponent's battlefield.
        # This function is called if the *original* player gets to keep the card.
        
        # If the card was not mindbugged, it goes to the original player's battlefield.
        # Check if the card is *already* on the battlefield (due to mindbugging).
        # We need to find the creature instance associated with `card_to_play.id`.
        
        # This assumes `_handle_mindbug_response` already put the creature in the correct place.
        # If the card is *not* found on the opponent's battlefield:
        found_on_opponent_bf = False
        for creature in game_state.battlefield[game_state.get_inactive_player().player_id]: # Inactive is potential mindbugger
            if creature.id == card_to_play.id:
                found_on_opponent_bf = True
                break
        
        if not found_on_opponent_bf:
            # Original player keeps it
            creature = Creature(card_to_play, original_player_id)
            game_state.battlefield[original_player_id].append(creature)
            print(f"{creature.name} enters {original_player_id}'s battlefield.")

            # Activate Play ability for the *original* player
            game_state = self.game_rules.activate_play_ability(game_state, creature, original_player_id)
        
        # The `GameEngine`'s role is to ensure `game_state.phase` is updated
        # and `game_state.active_player_id` is correct for the next action.
        # After playing a card (and resolving Mindbug phase), the turn usually ends.
        game_state.phase = "end_turn_phase" # Signal to main loop to end turn
        return game_state


    def _handle_attack_action(self, game_state: GameState, action: AttackAction) -> GameState:
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()

        # Find attacking creature
        attacking_creature: Optional[Creature] = None
        for creature in game_state.battlefield[player.player_id]:
            if creature.id == action.attacking_creature_id:
                attacking_creature = creature
                break

        if not attacking_creature or attacking_creature.is_exhausted:
            print(f"Error: Invalid attacking creature or it's exhausted: {action.attacking_creature_id}")
            return game_state
        
        if attacking_creature.has_attacked_this_turn and "Frenzy" not in attacking_creature.keywords:
            print(f"Error: {attacking_creature.name} already attacked this turn and doesn't have Frenzy.")
            return game_state

        attacking_creature.is_exhausted = True # Attacker becomes exhausted
        attacking_creature.has_attacked_this_turn = True # Mark it as attacked
        print(f"{player.player_id}'s {attacking_creature.name} attacks!")

        # Activate "Attack" abilities (e.g., Tusked Extorter)
        game_state = self.game_rules.activate_attack_ability(game_state, attacking_creature)

        # Check if opponent has a blocker (Mindbug rule: opponent can choose to block or take life)
        opponent_creatures = game_state.battlefield[opponent.player_id]
        
        # Filter valid blockers based on keywords (e.g., Sneaky)
        valid_blockers = [c for c in opponent_creatures if self.game_rules.is_creature_valid_blocker(attacking_creature, c)]

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
        # Action: Attacker chooses target (player or creature)
        # Then, if target is creature, or if target is player and opponent has blockers,
        # opponent gets to choose a blocker.
        
        # Let's assume for this example, the AttackAction implies either attacking player or creature.
        # If `action.target_id` is a player ID, it's a direct attack.
        # If `action.target_id` is a creature ID, it's an attack on that creature.

        target_creature: Optional[Creature] = None
        for creature in opponent_creatures:
            if creature.id == action.target_id:
                target_creature = creature
                break

        if target_creature:
            # Attacking a creature directly (Mindbug doesn't work this way, usually)
            # In Mindbug, you declare attack, opponent *chooses* to block or take life.
            # So `AttackAction` should only specify attacker, not target.
            # The GameEngine then asks for a `BlockAction`.

            # REVISED FLOW for Attack:
            # 1. Player declares `AttackAction(player_id, attacking_creature_id)`
            # 2. GameEngine processes this, sets `game_state.phase = "block_phase"`
            #    and stores `game_state._pending_attack_creature = attacking_creature`.
            # 3. GameEngine then expects `BlockAction` from inactive player.
            
            print(f"Error: Mindbug attack logic implies player declares attack, opponent chooses block/life. "
                  f"AttackAction target should not be a creature directly.")
            return game_state # This branch indicates a misunderstanding of Mindbug attack rules.
        
        else: # Attacking opponent directly
            print(f"{player.player_id}'s {attacking_creature.name} attacks {opponent.player_id} directly!")
            
            # Opponent decides to block or take life.
            # This is where the game engine would prompt the opponent's agent.
            # For now, let's assume if `target_id` is opponent_id, they *always* take life if they can't block.
            # Or, for simplicity for now, they take a life if no blocker was provided.
            
            # This state needs to be set up to receive a BlockAction.
            game_state.phase = "block_phase"
            game_state._pending_attack_creature = attacking_creature # Store for block decision
            game_state._current_attacker_player_id = player.player_id # Who is attacking
            print(f"Waiting for {opponent.player_id} to choose a blocker or take life.")
            return game_state # State is now waiting for block action

    def _handle_block_action(self, game_state: GameState, action: BlockAction) -> GameState:
        opponent = game_state.get_active_player() # Opponent is active during block phase
        active_player = game_state.get_inactive_player() # The player who attacked

        attacking_creature = game_state._pending_attack_creature
        if not attacking_creature or attacking_creature.id != action.attacking_creature_id:
            print("Error: No pending attack creature or ID mismatch for block action.")
            return game_state

        if action.blocking_creature_id:
            # Opponent chose to block
            blocking_creature: Optional[Creature] = None
            for creature in game_state.battlefield[opponent.player_id]:
                if creature.id == action.blocking_creature_id:
                    blocking_creature = creature
                    break
            
            if not blocking_creature or not self.game_rules.is_creature_valid_blocker(attacking_creature, blocking_creature):
                print(f"Error: Invalid blocking creature or not a valid blocker for {attacking_creature.name}.")
                return game_state

            print(f"{opponent.player_id}'s {blocking_creature.name} blocks {attacking_creature.name}.")
            
            # Resolve combat
            game_state, (defeated_attackers_ids, defeated_blockers_ids) = \
                self.game_rules.resolve_combat(game_state, attacking_creature, blocking_creature)

            # Update battlefield and discard pile
            # This needs to find the Creature objects by ID and move them.
            # For simplicity, this part will be a bit verbose:
            
            # Remove defeated from attacker's battlefield
            game_state.battlefield[active_player.player_id] = [
                c for c in game_state.battlefield[active_player.player_id] if c.id not in defeated_attackers_ids
            ]
            for defeated_id in defeated_attackers_ids:
                # Find the actual creature object to move to discard
                for c in game_state.battlefield[active_player.player_id]: # Re-search for the creature if it wasn't removed
                    if c.id == defeated_id:
                        active_player.discard_pile.append(c.card) # Move the base Card to discard
                        print(f"{c.name} (from {active_player.player_id}) was defeated and discarded.")
                        break # Found and processed
            
            # Remove defeated from blocker's battlefield
            game_state.battlefield[opponent.player_id] = [
                c for c in game_state.battlefield[opponent.player_id] if c.id not in defeated_blockers_ids
            ]
            for defeated_id in defeated_blockers_ids:
                # Find the actual creature object to move to discard
                for c in game_state.battlefield[opponent.player_id]: # Re-search for the creature if it wasn't removed
                    if c.id == defeated_id:
                        opponent.discard_pile.append(c.card) # Move the base Card to discard
                        print(f"{c.name} (from {opponent.player_id}) was defeated and discarded.")
                        break # Found and processed

        else:
            # Opponent chose not to block (or couldn't)
            print(f"{opponent.player_id} chooses not to block.")
            game_state = self.game_rules.lose_life(game_state, opponent.player_id, 1)

        # Clean up pending attack state
        del game_state._pending_attack_creature
        del game_state._current_attacker_player_id
        game_state.phase = "attack_resolution_phase" # Or just "main_phase" if player can attack again

        return game_state

    def _handle_end_turn_action(self, game_state: GameState, action: EndTurnAction) -> GameState:
        # Check if game is over before ending turn
        if game_state.is_game_over():
            return game_state

        print(f"{action.player_id} ends turn {game_state.turn_count}.")

        # Reset creature exhaustion for the active player's creatures at end of turn
        # (This is often done at start of *next* turn, but here for simplicity,
        # let's do it at the end of the current player's turn)
        for creature in game_state.battlefield[game_state.active_player_id]:
            creature.is_exhausted = False
            creature.has_attacked_this_turn = False # Reset attack flag too

        # Check for extra turn due to Mindbug
        if hasattr(game_state, '_pending_extra_turn_for') and game_state._pending_extra_turn_for == game_state.active_player_id:
            print(f"{game_state.active_player_id} gets an extra turn!")
            del game_state._pending_extra_turn_for # Clear the flag
            # Active player remains the same, phase resets for a new turn.
            game_state.phase = "draw_phase" # Or start_of_turn_phase
        else:
            # Normal turn progression: Switch active player, increment turn count
            game_state.switch_active_player()
            if game_state.active_player_id == game_state.players[game_state.initial_active_player_id].player_id: # Check if first player is active again
                 game_state.turn_count += 1 # Increment turn count only when initial active player starts new turn
            game_state.phase = "draw_phase" # Next player's turn starts with draw phase
        
        # After turn ends, refill hand if <5 (Mindbug rule)
        # This is also handled in play_creature, but let's make sure it happens here too.
        # This is a constant check in Mindbug.
        player = game_state.get_active_player() # The new active player
        while len(player.hand) < 5 and player.deck:
            drawn_card = player.draw_card()
            print(f"{player.player_id} draws {drawn_card.name} to refill hand.")

        return game_state

    def get_valid_actions(self, game_state: GameState) -> List[Action]:
        """
        Determines all legal actions the active player can take in the current game state.
        This is critical for AI and human input validation.
        """
        valid_actions: List[Action] = []
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()

        if game_state.game_over:
            return []

        if self.mindbug_phase_active:
            # If in Mindbug response phase, only Mindbug-related actions are valid for the opponent
            played_card_id = game_state._pending_mindbug_card_for_opponent.id
            if opponent.mindbugs:
                valid_actions.append(UseMindbugAction(inactive_player.player_id, played_card_id))
            valid_actions.append(PassMindbugAction(inactive_player.player_id))
            return valid_actions

        # Normal turn actions based on phase
        if game_state.phase == "draw_phase":
            # Player automatically draws. No action needed from player, engine handles this.
            # Immediately transition to play phase.
            # This method should probably not be called during auto-draw.
            # For simplicity, if called, suggest to end turn or play.
            valid_actions.append(EndTurnAction(active_player.player_id)) # Still an option
            for card in active_player.hand:
                valid_actions.append(PlayCreatureAction(active_player.player_id, card.id))

        elif game_state.phase == "play_phase":
            # Can play a card or end turn
            for card in active_player.hand:
                valid_actions.append(PlayCreatureAction(active_player.player_id, card.id))
            valid_actions.append(EndTurnAction(active_player.player_id))

        elif game_state.phase == "attack_phase":
            # Can attack with an unexhausted creature, or end turn
            for creature in game_state.battlefield[active_player.player_id]:
                if not creature.is_exhausted:
                    # Can attack player directly (if no blockers are forced)
                    valid_actions.append(AttackAction(active_player.player_id, creature.id, inactive_player.player_id))
                    # Or attack specific creatures if Hunter allows, or if it's a direct target
                    # (Mindbug doesn't generally allow targeting opponent's creatures directly like this for attacks)
            valid_actions.append(EndTurnAction(active_player.player_id))

        elif game_state.phase == "block_phase":
            # Opponent is making a blocking decision
            attacking_creature = game_state._pending_attack_creature
            if attacking_creature:
                # Option to not block
                valid_actions.append(BlockAction(inactive_player.player_id, attacking_creature.id, None))
                
                # Options to block with valid creatures
                for blocker in game_state.battlefield[inactive_player.player_id]:
                    if self.game_rules.is_creature_valid_blocker(attacking_creature, blocker):
                        valid_actions.append(BlockAction(inactive_player.player_id, attacking_creature.id, blocker.id))
            else:
                # Should not happen in "block_phase"
                print("Warning: block_phase entered without pending attack.")
            
        elif game_state.phase == "end_turn_phase":
            # Only option is to transition to next turn, which the engine does automatically
            # or the player signals it with an EndTurnAction if multiple actions allowed.
            valid_actions.append(EndTurnAction(active_player.player_id))


        # General rule: a player must take an action. If they cannot, they lose.
        if not valid_actions and not game_state.game_over:
            print(f"No valid actions for {active_player.player_id}. They lose by inability to act.")
            game_state.game_over = True
            game_state.winner_id = inactive_player.player_id # Opponent wins
            return [] # No valid actions

        return valid_actions