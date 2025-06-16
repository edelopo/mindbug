from typing import Dict, List, Optional, Any
import copy
from src.models.game_state import GameState
from src.models.action import *
from src.models.card import Card
import src.core.game_rules as GameRules
from src.agents.base_agent import BaseAgent

class GameEngine:
    def __init__(
            self,
            all_cards: List[Card] = [], 
            deck_size: int = 10, 
            hand_size: int = 5, 
            agents: Dict[str, BaseAgent] = {}
        ):
        self.all_cards = all_cards
        self.deck_size = deck_size
        self.hand_size = hand_size
        self.agents = agents
        self.action_dict = {
            "steal": {
                "action": StealAction,
                "handler": self._handle_steal_action,
            },
            "discard": {
                "action": DiscardAction,
                "handler": self._handle_discard_action,
            },
            "play_from_discard": {
                "action": PlayFromDiscardAction,
                "handler": self._handle_play_from_discard_action,
            },
            "defeat": {
                "action": DefeatAction,
                "handler": self._handle_defeat_action,
            },
            "hunt": {
                "action": HuntAction,
                "handler": self._handle_hunt_action,
            },
            "continue_attack": {
                "action": AttackAction,
                "handler": self._handle_attack_action,
            },
            "resolve_attack": {
                "action": AttackAction,
                "handler": self._handle_attack_action,
            },
            "frenzy_attack": {
                "action": AttackAction,
                "handler": self._handle_attack_action,
            },
            "frenzy": {
                "action": FrenzyAction,
                "handler": self._handle_frenzy_action,
            },
            "block": {
                "action": BlockAction,
                "handler": self._handle_block_action,
            },
            "mindbug": {
                "action": MindbugAction,
                "handler": self._handle_mindbug_response,
            },
        }

    def apply_action(self, game_state: GameState, action: Action) -> GameState:
        """
        Applies a player's action to the current game state and returns the new state.
        This is the core method for advancing the game.
        """
        if game_state.game_over:
            print("Game is already over. Cannot apply more actions.")
            return game_state

        new_state = copy.deepcopy(game_state)
        if action.player_id != new_state.active_player_id:
                raise ValueError(f"Wrong active player: {action}.")
        
        elif new_state._pending_action == "play_or_attack":
            if isinstance(action, PlayCardAction):
                return self._handle_play_card_action(new_state, action)
            elif isinstance(action, AttackAction):
                return self._handle_attack_action(new_state, action)
            else:
                raise ValueError(f"Invalid action type during {new_state._pending_action} phase: {type(action)}.")

        elif new_state._pending_action in self.action_dict.keys():
            action_type = self.action_dict[new_state._pending_action]["action"]
            handler = self.action_dict[new_state._pending_action]["handler"]
            if isinstance(action, action_type):
                return handler(new_state, action)
            else:
                raise ValueError(f"Invalid action type during {new_state._pending_action} phase: {type(action)}.")

        # elif new_state._pending_action == "block":
        #     if isinstance(action, BlockAction):
        #         return self._handle_block_action(new_state, action)
        #     else:
        #         raise ValueError(f"Invalid action type during {new_state._pending_action} phase: {type(action)}.")

        else:
            raise ValueError(f"Unknown pending action: {new_state._pending_action}. Cannot apply action {action}.")
    
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
        card_to_play = GameRules.get_card_by_uuid(game_state, action.card_uuid)
            
        # 1. Remove card from hand
        player.play_card(card_to_play) # player.play_card removes it from hand and adds it to play_area.
        print(f"{player.id} plays {card_to_play.name}.")

        # 2. Draw back to hand_size cards
        while len(player.hand) < self.hand_size and player.deck:
            drawn_card = player.draw_card()
        
        # 3. Opponent gets a chance to Mindbug
        if opponent.mindbugs:
            game_state._pending_mindbug_card_uuid = card_to_play.uuid # Store the card being played for Mindbug decision
            game_state._pending_action = "mindbug" # Set phase to mindbug
            game_state.switch_active_player() # Switch to opponent for Mindbug decision
            
            print(f"{opponent.id}, do you want to Mindbug {card_to_play.name}?")
            # The game loop will now wait for a UseMindbugAction or PassMindbugAction from the opponent.
        else:
            print(f"{opponent.id} has no Mindbugs left.")
            game_state = GameRules.activate_play_ability(game_state, card_to_play.uuid, self.agents)
        
        return game_state
    
    def _handle_play_from_discard_action(self, game_state: GameState, action: PlayFromDiscardAction) -> GameState:
        """
        Handles the action of playing a card from the discard pile.
        """
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()
        card = GameRules.get_card_by_uuid(game_state, action.card_uuid)
        
        if card in player.discard_pile:
            previous_owner = player
        elif card in opponent.discard_pile:
            previous_owner = opponent
        else:
            raise ValueError(f"Card with UUID {action.card_uuid} not found in either player's discard pile.")

        previous_owner.discard_pile.remove(card)
        player.play_area.append(card)
        card.controller = player
        print(f"{player.id} plays {card.name} from {previous_owner.id}'s discard pile.")
        game_state = GameRules.activate_play_ability(game_state, card.uuid, self.agents)

        return game_state

    def _handle_mindbug_response(self, game_state: GameState, action: MindbugAction) -> GameState:
        opponent = game_state.get_active_player() # In mindbug phase, the "active" player is the opponent.
        player = game_state.get_inactive_player() # The player who originally played the card.
        # Get the card pending Mindbug response
        if game_state._pending_mindbug_card_uuid:
            played_card = GameRules.get_card_by_uuid(game_state, game_state._pending_mindbug_card_uuid)
        else:
            raise ValueError("No pending Mindbug card UUID found in game state.")

        if not played_card:
            raise ValueError("No played card found for Mindbug response.")
        if action.player_id != opponent.id:
            raise ValueError(f"Action player {action.player_id} is not the active player {opponent.id} during Mindbug phase.")
        
        if action.use_mindbug:
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
                raise ValueError(f"{opponent.id} tried to use Mindbug but has no Mindbugs left.")
        else:
            print(f"{opponent.id} passes on Mindbugging {played_card.name}.")
            game_state.switch_active_player() # Switch back to original player
            game_state = GameRules.activate_play_ability(game_state, played_card.uuid, self.agents)

        game_state._pending_mindbug_card_uuid = None # Clear pending Mindbug state

        return game_state

    def _handle_attack_action(self, game_state: GameState, action: AttackAction) -> GameState:
        attacking_player = game_state.get_active_player()
        blocking_player = game_state.get_inactive_player()
        attacking_card = GameRules.get_card_by_uuid(game_state, action.attacking_card_uuid)
        if attacking_card not in attacking_player.play_area:
            raise ValueError(f"Attacking card {attacking_card.name} not found in {attacking_player.id}'s play area.")

        if game_state._pending_action in ["play_or_attack", "frenzy_attack"]:
            # This is the first part of the phase, so activate "Attack" abilities
            print(f"{attacking_player.id}'s {attacking_card.name} attacks!")
            game_state._pending_attack_card_uuid = attacking_card.uuid
            game_state = GameRules.activate_attack_ability(game_state, attacking_card.uuid, self.agents)
            return game_state
        
        elif game_state._pending_action == "continue_attack":
            # This is the second part of the phase, where we resolve the attack
            if ("Hunter" in GameRules.get_effective_keywords(game_state, attacking_card.uuid)
                and not game_state._already_hunted):
                valid_targets = [card.uuid for card in blocking_player.play_area]
                if not valid_targets:
                    game_state._pending_action = "resolve_attack"
                else:
                    game_state._valid_targets = valid_targets
                    game_state._pending_action = "hunt"
                return game_state
            # If there is no Hunter ability or it has already been used, move on to choosing a blocker
            else:
                valid_blockers: List[UUID] = []
                for card in blocking_player.play_area:
                    if GameRules.is_valid_blocker(
                        blocking_card_uuid=card.uuid, 
                        attacking_card_uuid=attacking_card.uuid, 
                        game_state=game_state,
                    ):
                        valid_blockers.append(card.uuid)
                
                if not valid_blockers:
                    game_state._pending_action = "resolve_attack"
                else:
                    game_state.switch_active_player() # Switch to opponent for blocking decision
                    game_state._valid_targets = valid_blockers
                    game_state._pending_action = "block"
                return game_state
        
        elif game_state._pending_action == "resolve_attack":
            if not game_state._pending_block_card_uuid:
                # No blocker was chosen, opponent takes damage
                print(f"{blocking_player.id} does not block. {attacking_player.id} deals damage directly!")
                game_state = self.lose_life(game_state, blocking_player.id)
            else:
                blocking_card = GameRules.get_card_by_uuid(game_state, game_state._pending_block_card_uuid)
                if blocking_card not in blocking_player.play_area:
                    raise ValueError(f"Blocking card {blocking_card.name} not found in {blocking_player.id}'s play area.")
                print(f"{blocking_card.name} and {attacking_card.name} face each other.")
                # Resolve combat
                game_state = GameRules.resolve_combat(game_state, attacking_card.uuid, blocking_card.uuid, self.agents)
                game_state._pending_block_card_uuid = None # Clear pending block card UUID
                game_state._already_hunted = False # Reset hunting state

            attacking_player = game_state.get_player(attacking_player.id) # Refresh player state after combat resolution
            attacking_card = GameRules.get_card_by_uuid(game_state, action.attacking_card_uuid)
            if ("Frenzy" in GameRules.get_effective_keywords(game_state, attacking_card.uuid) 
                and not game_state._frenzy_active # Ensure Frenzy has not already been activated
                and attacking_card in attacking_player.play_area # Ensure the card has not been defeated
            ):
                game_state._pending_action = "frenzy"
                game_state._frenzy_active = True
                return game_state
            else:
                game_state._frenzy_active = False
                game_state._pending_attack_card_uuid = None
                game_state._pending_block_card_uuid = None
                game_state._already_hunted = False 
                game_state = self.end_turn(game_state)
                return game_state
        
        else:
            raise ValueError(f"Unknown pending action: {game_state._pending_action}. Cannot handle attack action {action}.")

    def _handle_block_action(self, game_state: GameState, action: BlockAction) -> GameState:
        """
        Handles the blocking action when a player has choose whether to block an attack or not.
        """
        blocking_player = game_state.get_active_player()
        attacking_player = game_state.get_inactive_player()
        
        if not game_state._pending_attack_card_uuid:
            raise ValueError("No pending attack card to block.")

        attacking_card = GameRules.get_card_by_uuid(game_state, game_state._pending_attack_card_uuid)

        if action.blocking_card_uuid:
            blocking_card = GameRules.get_card_by_uuid(game_state, action.blocking_card_uuid)
            if blocking_card not in blocking_player.play_area:
                raise ValueError(f"Blocking card {blocking_card.name} not found in {blocking_player.id}'s play area.")
            print(f"{blocking_player.id} blocks {attacking_card.name} with {blocking_card.name}.")
            game_state._pending_block_card_uuid = blocking_card.uuid
        
        game_state._pending_action = "resolve_attack"
        game_state.switch_active_player() # Switch to attacking player to resolve the attack
        return game_state

    def _handle_defeat_action(self, game_state: GameState, action: DefeatAction) -> GameState:
        """
        Handles the defeat action when a player chooses to defeat cards from their opponent.
        """
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()

        if action.player_id != player.id:
            raise ValueError(f"Action player {action.player_id} is not the active player {player.id}.")

        game_state = GameRules.defeat(game_state, action.card_uuids, self.agents)            

        # Clear the auxiliary variables used for defeating
        game_state._valid_targets = None
        game_state._amount_of_targets = None

        if game_state._return_to_attack:
            game_state._pending_action = "continue_attack"
            game_state._return_to_attack = False
        else:
            game_state._pending_action = "finish_action"
        return game_state
        
    def _handle_steal_action(self, game_state: GameState, action: StealAction) -> GameState:
        """
        Handles the stealing action when a player chooses to steal cards from their opponent.
        """
        stealing_player = game_state.get_active_player()
        target_player = game_state.get_inactive_player()

        if action.player_id != stealing_player.id:
            raise ValueError(f"Action player {action.player_id} is not the active player {stealing_player.id}.")

        for card_uuid in action.card_uuids:
            if card_uuid not in [card.uuid for card in target_player.play_area]:
                raise ValueError(f"Card with UUID {card_uuid} not found in {target_player.id}'s play area.")

            card = GameRules.get_card_by_uuid(game_state, card_uuid)
            # 1. Remove the card from the target player's play area
            target_player.play_area.remove(card)
            # 2. Add the card to the stealing player's play area
            stealing_player.play_area.append(card)
            card.controller = stealing_player
            print(f"{stealing_player.id} steals {card.name} from {target_player.id}.")

        # Clear the auxiliary variables used for stealing
        game_state._valid_targets = None
        game_state._amount_of_targets = None

        game_state._pending_action = "finish_action"
        return game_state
    
    def _handle_discard_action(self, game_state: GameState, action: DiscardAction) -> GameState:
        """
        Handles the discard action when a player has to discard a card.
        """
        player = game_state.get_active_player()
        if action.player_id != player.id:
            raise ValueError(f"Action player {action.player_id} is not the active player {player.id}.")
        
        for card_uuid in action.card_uuids:
            if card_uuid not in [card.uuid for card in player.hand]:
                raise ValueError(f"Card with UUID {card_uuid} not found in {player.id}'s hand.")

            card = GameRules.get_card_by_uuid(game_state, card_uuid)
            player.discard_card(card)
            print(f"{player.id} discards {card.name}.")

        # Clear the auxiliary variables used for discarding
        game_state._valid_targets = None
        game_state._amount_of_targets = None

        if game_state._return_to_attack:
            game_state._pending_action = "continue_attack"
            game_state.switch_active_player()
            game_state._return_to_attack = False
        else:
            game_state._pending_action = "finish_action"
        return game_state

    def _handle_hunt_action(self, game_state: GameState, action: HuntAction) -> GameState:
        """
        Handles the hunt action when a player chooses to hunt a card.
        """
        player = game_state.get_active_player()
        opponent = game_state.get_inactive_player()
        if action.player_id != player.id:
            raise ValueError(f"Action player {action.player_id} is not the active player {player.id}.")
        
        if action.card_uuid is None:
            game_state._already_hunted = True
            game_state._pending_action = "continue_attack"

        elif action.card_uuid not in [card.uuid for card in opponent.play_area]:
            raise ValueError(f"Card with UUID {action.card_uuid} not found in {opponent.id}'s play area.")
        
        else: 
            game_state._pending_block_card_uuid = action.card_uuid
            game_state._already_hunted = True
            game_state._pending_action = "resolve_attack"
            # Clear the auxiliary variables used for hunting
            game_state._valid_targets = None
        
        return game_state

    def _handle_frenzy_action(self, game_state: GameState, action: FrenzyAction) -> GameState:
        """
        Handles the frenzy action when a player chooses to activate Frenzy or not.
        """
        player = game_state.get_active_player()

        if action.player_id != player.id:
            raise ValueError(f"Action player {action.player_id} is not the active player {player.id}.")
        if not game_state._pending_attack_card_uuid:
            raise ValueError("No pending attack card UUID found in game state to activate Frenzy.")
        attacking_card = GameRules.get_card_by_uuid(game_state, game_state._pending_attack_card_uuid)
        if "Frenzy" not in GameRules.get_effective_keywords(game_state, attacking_card.uuid):
            raise ValueError(f"{attacking_card.name} does not have Frenzy ability.")

        if action.go_again:
            print(f"{player.id} activates Frenzy on {attacking_card.name}!")
            game_state._pending_action = "frenzy_attack"
            game_state._frenzy_active = True
        else:
            game_state = self.end_turn(game_state)

        return game_state

    # --- End Turn ---

    def end_turn(self, game_state: GameState) -> GameState:
        # Check if game is over before ending turn
        if game_state.is_game_over():
            return game_state
        
        print(f"Turn {game_state.turn_count} ended.\n")
        game_state.switch_active_player() # Switch active player
        game_state.turn_count += 1 # Increment turn count
        game_state._pending_action = "play_or_attack" # Go back to play/attack phase

        return game_state

    # --- Check of possible actions ---

    def get_valid_actions(self, game_state: GameState) -> List[Dict[str, Any]]:
        """
        Determines all legal actions the active player can take in the current game state.
        This is critical for AI and human input validation.
        """
        valid_actions: List[Dict[str, Any]] = []
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()

        if game_state.game_over:
            return []

        if game_state._pending_action == "mindbug":
            # During the mindbug phase, the active player must choose whether to use a mindbug or not.
            if not active_player.mindbugs:
                raise ValueError(f"Entered Mindbug phase but {active_player.id} has no Mindbugs left to use.")
            if not game_state._pending_mindbug_card_uuid:
                raise ValueError("Mindbug phase entered without a pending Mindbug card.")

            valid_actions.append({'action': MindbugAction(active_player.id, use_mindbug=True)})
            valid_actions.append({'action': MindbugAction(active_player.id, use_mindbug=False)})

        elif game_state._pending_action == "play_or_attack":
            # During the play phase, the active player can play a card or attack with a card on the play area.
            for card in active_player.hand:
                valid_actions.append({'action': PlayCardAction(active_player.id, card.uuid),
                                      'card_name': card.name})
            for card in active_player.play_area:
                valid_actions.append({'action': AttackAction(active_player.id, card.uuid),
                                      'card_name': card.name})
                
        elif game_state._pending_action == "block":
            # During the block phase, the active player can choose to block an attack with one of their cards.
            if not game_state._valid_targets:
                raise ValueError("No valid targets for blocking action.")
            for card_uuid in game_state._valid_targets:
                valid_actions.append({'action': BlockAction(active_player.id, card_uuid),
                                      'card_name': GameRules.get_card_by_uuid(game_state, card_uuid).name})
            valid_actions.append({'action': BlockAction(active_player.id, None)})

        elif game_state._pending_action == "steal":
            # During the steal phase, the active player can choose to steal cards among the valid targets.
            if not game_state._valid_targets:
                raise ValueError("No valid targets for stealing action.")
            if not game_state._amount_of_targets:
                raise ValueError("No amount of targets specified for stealing action.")
            
            valid_targets = game_state._valid_targets
            if isinstance(game_state._amount_of_targets, int):
                min_size = max_size = min(game_state._amount_of_targets, len(valid_targets))
            else:
                min_size = min(game_state._amount_of_targets[0], len(valid_targets))
                max_size = min(game_state._amount_of_targets[1], len(valid_targets))

            valid_target_lists = self.list_of_subsets(valid_targets, min_size=min_size, max_size=max_size)
            for target_list in valid_target_lists:
                valid_actions.append({'action': StealAction(active_player.id, target_list),
                                      'card_names': [GameRules.get_card_by_uuid(game_state, uuid).name for uuid in target_list]})
                
        elif game_state._pending_action == "discard":
            # During the discard phase, the active player can choose which cards from hand to discard.
            if not game_state._valid_targets:
                raise ValueError("No valid targets for stealing action.")
            if not game_state._amount_of_targets:
                raise ValueError("No amount of targets specified for discard action.")
            
            valid_targets = game_state._valid_targets
            if isinstance(game_state._amount_of_targets, int):
                min_size = max_size = min(game_state._amount_of_targets, len(valid_targets))
            else:
                min_size = min(game_state._amount_of_targets[0], len(valid_targets))
                max_size = min(game_state._amount_of_targets[1], len(valid_targets))

            valid_target_lists = self.list_of_subsets(valid_targets, min_size=min_size, max_size=max_size)
            for target_list in valid_target_lists:
                valid_actions.append({'action': DiscardAction(active_player.id, target_list),
                                      'card_names': [GameRules.get_card_by_uuid(game_state, uuid).name for uuid in target_list]})
                
        elif game_state._pending_action == "defeat":
            # During the discard phase, the active player can choose which cards to defeat.
            if not game_state._valid_targets:
                raise ValueError("No valid targets for stealing action.")
            if not game_state._amount_of_targets:
                raise ValueError("No amount of targets specified for defeat action.")
            
            valid_targets = game_state._valid_targets
            if isinstance(game_state._amount_of_targets, int):
                min_size = max_size = min(game_state._amount_of_targets, len(valid_targets))
            else:
                min_size = min(game_state._amount_of_targets[0], len(valid_targets))
                max_size = min(game_state._amount_of_targets[1], len(valid_targets))

            valid_target_lists = self.list_of_subsets(valid_targets, min_size=min_size, max_size=max_size)
            for target_list in valid_target_lists:
                valid_actions.append({'action': DefeatAction(active_player.id, target_list),
                                      'card_names': [GameRules.get_card_by_uuid(game_state, uuid).name for uuid in target_list]})
            
        elif game_state._pending_action == "play_from_discard":
            # During the play from discard phase, the active player can play cards 
            # either from their discard pile or from the opponent's discard pile.
            if not game_state._valid_targets:
                raise ValueError("No valid targets for stealing action.")
            if not game_state._amount_of_targets:
                raise ValueError("No amount of targets specified for stealing action.")
            if game_state._amount_of_targets != 1:
                raise NotImplementedError("Currently only one card can be played from discard at a time.")
            
            for card_uuid in game_state._valid_targets:
                valid_actions.append({'action': PlayFromDiscardAction(active_player.id, card_uuid),
                                      'card_name': GameRules.get_card_by_uuid(game_state, card_uuid).name})
                
        elif game_state._pending_action == "hunt":
            # During the hunt phase, the active player can choose to hunt a card from the opponent's play area.
            if not game_state._valid_targets:
                raise ValueError("No valid targets for hunting action.")
            
            for card_uuid in game_state._valid_targets:
                valid_actions.append({'action': HuntAction(active_player.id, card_uuid),
                                      'card_name': GameRules.get_card_by_uuid(game_state, card_uuid).name})
                
        elif game_state._pending_action == "frenzy":
            # During the frenzy phase, the active player can choose to activate Frenzy or not.
            if not game_state._pending_attack_card_uuid:
                raise ValueError("No pending attack card UUID found in game state to activate Frenzy.")
            attacking_card = GameRules.get_card_by_uuid(game_state, game_state._pending_attack_card_uuid)
            if "Frenzy" in GameRules.get_effective_keywords(game_state, attacking_card.uuid):
                valid_actions.append({'action': FrenzyAction(active_player.id, go_again=True),
                                      'card_name': attacking_card.name})
                valid_actions.append({'action': FrenzyAction(active_player.id, go_again=False),
                                      'card_name': attacking_card.name})
            else:
                raise ValueError(f"{attacking_card.name} does not have Frenzy ability.")

        else:
            raise ValueError(f"Unknown pending action: {game_state._pending_action}. Cannot determine valid actions.")

        # General rule: a player must take an action. If they cannot, they lose.
        if not valid_actions and not game_state.game_over:
            print(f"No valid actions for {active_player.id}. They lose by inability to act.")
            game_state.game_over = True
            game_state.winner_id = inactive_player.id # Opponent wins
            return [] # No valid actions

        return valid_actions
    
    # --- Helper functions ---
    
    @staticmethod
    def list_of_subsets(original_list: List, min_size: int, max_size: int) -> List[List]:
        """
        Generates all subsets of the original list with sizes between min_size and max_size.
        """
        from itertools import combinations
        subsets = []
        for size in range(min_size, max_size + 1):
            subsets.extend(combinations(original_list, size))
        return [list(subset) for subset in subsets]
    
    # --- Play a full game and return the history ---

    def play_game(
            self,
            p1_forced_card_ids: List[str] = [],
            p2_forced_card_ids: List[str] = []
        ) -> Dict:
        """
        Plays a full game with the current agents and returns the final game state as a Dict.
        """

        logs = {}

        # Make a list of forced cards (for testing purposes)
        p1_forced_cards = []
        for card_id in p1_forced_card_ids:
            for card in self.all_cards:
                if card.id == card_id:
                    p1_forced_cards.append(card)
                    break
            else:
                raise ValueError(f"Forced card ID '{card_id}' not found in all cards.")
        p2_forced_cards = []
        for card_id in p2_forced_card_ids:
            for card in self.all_cards:
                if card.id == card_id:
                    p2_forced_cards.append(card)
                    break
            else:
                raise ValueError(f"Forced card ID '{card_id}' not found in all cards.")
        
        player1_id=list(self.agents.keys())[0]
        player2_id=list(self.agents.keys())[1]

        game_state = GameState.initial_state(
            player1_id=player1_id,
            player2_id=player2_id,
            all_cards=self.all_cards,
            deck_size=self.deck_size,
            hand_size=self.hand_size,
            p1_forced_cards=p1_forced_cards,
            p2_forced_cards=p2_forced_cards
        )

        p1_initial_deck = {str(card.uuid): card.id 
                           for card in game_state.get_player(player1_id).hand + game_state.get_player(player1_id).deck}
        p2_initial_deck = {str(card.uuid): card.id
                           for card in game_state.get_player(player2_id).hand + game_state.get_player(player2_id).deck}

        logs['agents'] = {
            player1_id: type(self.agents[player1_id]).__name__,
            player2_id: type(self.agents[player2_id]).__name__  # This is temporary, we should have a better way to label agents.
        }

        logs['initial_decks'] = {
            player1_id: p1_initial_deck,
            player2_id: p2_initial_deck
        }
        logs['history'] = []

        while not game_state.game_over:
            if game_state._pending_action == "finish_action":
                if game_state._switch_active_player_back:
                    game_state.switch_active_player()
                    game_state._switch_active_player_back = False # Reset the flag
                game_state = self.end_turn(game_state)
                continue
                
            if game_state._pending_action in ["continue_attack", "resolve_attack", "frenzy_attack"]:
                if not game_state._pending_attack_card_uuid:
                    raise ValueError("No pending attack card UUID found in game state to continue attack action.")
                attack_card = GameRules.get_card_by_uuid(game_state, game_state._pending_attack_card_uuid)
                if not attack_card.controller:
                    raise ValueError(f"Attack card {attack_card.name} has no controller.")
                game_state = self.apply_action(game_state, AttackAction(attack_card.controller.id, attack_card.uuid))
                continue

            active_player_id = game_state.active_player_id
            active_agent = self.agents[active_player_id]

            valid_actions = self.get_valid_actions(game_state)
            
            if not valid_actions:
                print(f"{active_player_id} has no valid actions and loses!")
                game_state.game_over = True
                game_state.winner_id = game_state.inactive_player_id
                break

            action = active_agent.choose_action(game_state, valid_actions)
            logs['history'].append({
                "turn": game_state.turn_count,
                "action": str(action),
            })
            game_state = self.apply_action(game_state, action)

        for player in game_state.players.values():
            if player.life_points <= 0:
                win_condition = "life_below_zero"
                break
        else:
            win_condition = "run_out_of_actions"

        logs['final_state'] = {
            "active_player_id": game_state.active_player_id,
            "inactive_player_id": game_state.inactive_player_id,
            "turn_count": game_state.turn_count,
            "game_over": game_state.game_over,
            "winner_id": game_state.winner_id,
            "win_condition": win_condition,
            "players": {
                player.id: {
                    "life_points": player.life_points,
                    "hand": [str(card.uuid) for card in player.hand],
                    "play_area": [str(card.uuid) for card in player.play_area],
                    "discard_pile": [str(card.uuid) for card in player.discard_pile],
                    "deck_size": len(player.deck),
                    "mindbugs": player.mindbugs
                } for player in game_state.players.values()
            }
        }

        return logs