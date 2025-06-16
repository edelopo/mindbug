# CLI = Command Line Interface
from src.models.game_state import GameState
from src.models.action import *
from src.models.card import Card
from uuid import UUID
from typing import List, Dict
import src.core.game_rules as GameRules
import os

class MindbugCLI:
    width = 140  # Width of the display area

    def get_effective_keyword_initials(self, game_state, card_uuid: UUID) -> str:
        """
        Returns a string of keyword initials for the given card.
        """
        keywords = GameRules.get_effective_keywords(game_state, card_uuid)
        if not keywords:
            return "None"
        initials = [keyword[0].upper() for keyword in keywords]
        return ",".join(initials)
    
    def get_string_effective_keywords(self, game_state, card_uuid: UUID) -> str:
        """
        Returns a string of effective keywords for the given card.
        """
        keywords = GameRules.get_effective_keywords(game_state, card_uuid)
        if not keywords:
            return "None"
        return ", ".join(keywords)
    
    def get_string_keywords(self, card: Card) -> str:
        """
        Returns a string of keywords for the given card.
        """
        if not card.keywords:
            return "None"
        return ", ".join(card.keywords)

    def display_game_state(self, game_state: GameState):
        """
        Displays the current state of the game to the console with improved formatting.
        """
        active_player = game_state.get_active_player()
        inactive_player = game_state.get_inactive_player()

        # os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for better readability

        # Game header with turn info
        print("\n" + "╔" + "═"*(self.width-2) + "╗")
        print(f"║{'TURN ' + str(game_state.turn_count) + ' - PENDING ACTION: ' + game_state._pending_action.upper():^{self.width-2}}║")
        print("╚" + "═"*(self.width-2) + "╝")

        # Active player indicator
        print(f"\n▶ {active_player.id} IS THE ACTIVE PLAYER ◀")

        # Active player's board
        print(f"\n┌{'─'*(self.width-2)}┐")
        print(f"│ {active_player.id}'s Board{' '*((self.width-2) - len(active_player.id) - 9)}│")
        print(f"├{'─'*(self.width-2)}┤")
        # Calculate equal column width based on total width
        col_width = (self.width - 2) // 4
        rest = f"{'Mindbugs: ' + str(active_player.mindbugs):^{col_width}}│{'Deck: ' + str(len(active_player.deck)):^{col_width}}│{'Discard: ' + str(len(active_player.discard_pile)):^{col_width}}"
        print(f"│{'Life: ' + str(active_player.life_points):^{self.width - len(rest) - 3}}│{rest}│")
        print(f"├{'─'*(self.width-2)}┤")
        
        # Hand display
        print(f"│ Hand ({len(active_player.hand)} cards):{' '*((self.width-2) - len(f'Hand ({len(active_player.hand)} cards):') - 1)}│")
        if active_player.hand:
            for i, card in enumerate(active_player.hand):
                power_and_keywords = f"(P:{card.power:2d}, K: {self.get_string_keywords(card)})"
                card_str = f"  {i+1}. {card.name:<25} {power_and_keywords:<20} {card.ability_text}"
                print(f"│{card_str}{' '*(self.width - 2 - len(card_str))}│")
        else:
            print(f"│  (Empty){' '*(self.width-11)}│")
        
        # Play area display
        print(f"├{'─'*(self.width-2)}┤")
        print(f"│ Play Area ({len(active_player.play_area)} cards):{' '*((self.width-2) - len(f'Play Area ({len(active_player.play_area)} cards):') - 1)}│")
        if active_player.play_area:
            for i, card in enumerate(active_player.play_area):
                exhausted = "⚠ EXHAUSTED " if card.is_exhausted else ""
                eff_power = GameRules.get_effective_power(game_state, card.uuid)
                eff_keywords = self.get_string_effective_keywords(game_state, card.uuid)
                power_and_keywords = f"(P:{eff_power:2d}, K: {eff_keywords})"
                card_str = f"  {i+1}. {card.name:<25} {power_and_keywords:<20} {exhausted}{card.ability_text}"
                print(f"|{card_str}{' '*(self.width - 2 - len(card_str))}│")
        else:
            print(f"│  (Empty){' '*(self.width-11)}│")
        print(f"└{'─'*(self.width-2)}┘")

        # Inactive player's board
        print(f"\n┌{'─'*(self.width-2)}┐")
        print(f"│ {inactive_player.id}'s Board{' '*((self.width-2) - len(inactive_player.id) - 9)}│")
        print(f"├{'─'*(self.width-2)}┤")
        col_width = (self.width - 2) // 4
        rest = f"{'Mindbugs: ' + str(inactive_player.mindbugs):^{col_width}}│{'Deck: ' + str(len(inactive_player.deck)):^{col_width}}│{'Discard: ' + str(len(inactive_player.discard_pile)):^{col_width}}"
        print(f"│{'Life: ' + str(inactive_player.life_points):^{self.width - len(rest) - 3}}│{rest}│")
        print(f"├{'─'*(self.width-2)}┤")
        print(f"│ Hand: {len(inactive_player.hand)} cards{' '*((self.width-2) - len(f'Hand: {len(inactive_player.hand)} cards') - 1)}│")
        
        # Play area display
        print(f"├{'─'*(self.width-2)}┤")
        print(f"│ Play Area ({len(inactive_player.play_area)} cards):{' '*((self.width-2) - len(f'Play Area ({len(inactive_player.play_area)} cards):') - 1)}│")
        if inactive_player.play_area:
            for i, card in enumerate(inactive_player.play_area):
                exhausted = "⚠ EXHAUSTED" if card.is_exhausted else ""
                eff_power = GameRules.get_effective_power(game_state, card.uuid)
                eff_keywords = self.get_string_effective_keywords(game_state, card.uuid)
                power_and_keywords = f"(P:{eff_power:2d}, K: {eff_keywords})"
                card_str = f"  {i+1}. {card.name:<25} {power_and_keywords:<20} {exhausted} {card.ability_text}"
                print(f"|{card_str}{' '*(self.width - 2 - len(card_str))}│")
        else:
            print(f"│  (Empty){' '*(self.width-11)}│")
        print(f"└{'─'*(self.width-2)}┘\n")

    def get_player_action(self, possible_actions: List[Dict[str, Action | str]]) -> Action:
        """
        Prompts the human player to choose an action from a list of possibilities.
        """
        print("\nPossible actions:")

        def get_action_string(action: Action | str) -> str:
            if isinstance(action, PlayCardAction):
                return "Play"
            elif isinstance(action, AttackAction):
                return "Attack"
            elif isinstance(action, BlockAction):
                if not action.blocking_card_uuid:
                    return "Don't Block"
                return "Block"
            elif isinstance(action, StealAction):
                return "Steal"
            elif isinstance(action, MindbugAction):
                if action.use_mindbug:
                    return "Use Mindbug"
                else:
                    return "Don't Use Mindbug"
            elif isinstance(action, PlayFromDiscardAction):
                return "Play from Discard"
            elif isinstance(action, DiscardAction):
                return "Discard"
            elif isinstance(action, DefeatAction):
                return "Defeat"
            elif isinstance(action, HuntAction):
                return "Hunt"
            elif isinstance(action, FrenzyAction):
                if action.go_again:
                    return "Attack again"
                else:
                    return "Stop attacking"
            else:
                return "Unknown Action"

        for i, action in enumerate(possible_actions):
            if 'card_name' in action.keys():
                print(f"{i + 1}. {get_action_string(action['action'])} - {action['card_name']}")
            elif 'card_names' in action.keys():
                print(f"{i + 1}. {get_action_string(action['action'])} - {action['card_names']}")
            else:
                print(f"{i + 1}. {get_action_string(action['action'])}")

        while True:
            try:
                choice = input("Enter the number of your chosen action: ")
                action_index = int(choice) - 1
                if 0 <= action_index < len(possible_actions):
                    action = possible_actions[action_index]['action']
                    if isinstance(action, Action):
                        return action
                    else:
                        raise ValueError("Invalid action type.")
                else:
                    print("❌ Invalid action number. Please try again.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")