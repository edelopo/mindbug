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
        print(f"║{'TURN ' + str(game_state.turn_count) + ' - PHASE: ' + game_state.phase.upper():^{self.width-2}}║")
        print("╚" + "═"*(self.width-2) + "╝")

        # Active player indicator
        print(f"\n▶ {active_player.id}'s TURN")

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
                return f"Play"
            elif isinstance(action, AttackAction):
                return f"Attack"
            elif isinstance(action, BlockAction):
                return f"Block"
            elif isinstance(action, UseMindbugAction):
                return "Use Mindbug"
            elif isinstance(action, PassMindbugAction):
                return "Pass Mindbug"
            else:
                return "Unknown Action"

        for i, action in enumerate(possible_actions):
            if 'card_name' in action.keys():
                print(f"{i + 1}. {get_action_string(action['action'])} - Card: {action['card_name']}")
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

    def get_card_choice(self, game_state: GameState, choice_request: CardChoiceRequest) -> List[Card]:
        """
        Prompts the player to select cards from the given options.
        """
        # Card selection header with decorative box
        print("\n" + "╔" + "═"*(self.width-2) + "╗")
        print(f"║{'CARD SELECTION':^{self.width-2}}║")
        print("╚" + "═"*(self.width-2) + "╝")
        
        # Display the prompt
        print(f"\n{choice_request.prompt}")
        
        # Display card options in a formatted box
        print(f"\n┌{'─'*(self.width-2)}┐")
        print(f"│ Available Options:{' '*((self.width-2) - len('Available Options:') - 1)}│")
        print(f"├{'─'*(self.width-2)}┤")
        for i, card in enumerate(choice_request.options):
            exhausted = "⚠ EXHAUSTED" if card.is_exhausted else ""
            eff_power = GameRules.get_effective_power(game_state, card.uuid)
            card_str = f"  {i+1}. {card.name:<25} (P:{eff_power:2d}) {exhausted}"
            print(f"│{card_str}{' '*(self.width - 2 - len(card_str))}│")
        print(f"└{'─'*(self.width-2)}┘")
        
        # Selection instructions
        # print(f"\nSelect up to {choice_request.max_choices} card{'' if choice_request.max_choices == 1 else 's'} to {choice_request.purpose}.")
        
        # Get user input with error handling
        while True:
            try:
                indices = input("\nEnter your choice(s) (comma separated): ")
                chosen_indices = [int(idx.strip())-1 for idx in indices.split(",") if idx.strip()]
                chosen_indices = list(dict.fromkeys(chosen_indices))  # Remove duplicates preserving order
                
                # Validate choices
                if not chosen_indices and choice_request.min_choices > 0:
                    print("❌ No valid choices made. Please select at least one option.")
                    continue
                    
                if len(chosen_indices) > choice_request.max_choices:
                    print(f"❌ Too many selections. Please choose at most {choice_request.max_choices}.")
                    continue

                if len(chosen_indices) < choice_request.min_choices:
                    print(f"❌ Too few selections. Please choose at least {choice_request.min_choices}.")
                    continue
                
                invalid_indices = [i for i in chosen_indices if i < 0 or i >= len(choice_request.options)]
                if invalid_indices:
                    print(f"❌ Invalid selection(s): {[i+1 for i in invalid_indices]}. Try again.")
                    continue
                
                # Return valid selections
                chosen = [choice_request.options[i] for i in chosen_indices]
                return chosen
                
            except ValueError:
                print("❌ Please enter valid numbers separated by commas.")