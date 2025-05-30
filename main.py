# main.py (no significant changes needed here, as HumanAgent now uses CLI)
from src.core.game_engine import GameEngine
from src.models.game_state import GameState
from src.agents.human_agent import HumanAgent
from src.utils.data_loader import load_cards_from_json, load_definitions_from_json
from src.models.action import EndTurnAction # Ensure this is imported if used
import os

def run_game():
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    
    all_cards_list = load_cards_from_json(filepath=cards_json_path)
    card_definitions_dict = load_definitions_from_json(filepath=cards_json_path)

    game_engine = GameEngine(card_definitions=card_definitions_dict)

    player1_id = "Human Player 1"
    player2_id = "Human Player 2"
    game_state = GameState.initial_state(player1_id, player2_id, all_cards_list)

    human_agent1 = HumanAgent(player1_id)
    human_agent2 = HumanAgent(player2_id)
    agents = {player1_id: human_agent1, player2_id: human_agent2}

    print("--- Starting Mindbug Game ---")
    
    while not game_state.game_over:
        active_player_id = game_state.active_player_id
        active_agent = agents[active_player_id]

        print(f"\n--- It's {active_player_id}'s Turn (Phase: {game_state.phase}) ---")

        possible_actions = game_engine.get_possible_actions(game_state)
        
        if not possible_actions and not game_state.game_over:
            print(f"{active_player_id} has no valid actions and loses!")
            game_state.game_over = True
            game_state.winner_id = game_state.inactive_player_id
            break

        chosen_action = active_agent.choose_action(game_state, possible_actions)

        game_state = game_engine.apply_action(game_state, chosen_action)

        if isinstance(chosen_action, EndTurnAction):
            print(f"{active_player_id} ends their turn.")
            game_state.switch_active_player()
            game_state.turn_count += 1
            game_state.phase = "play_phase" # Reset phase for next player

        if game_state.game_over:
            print(f"\n--- Game Over! ---")
            if game_state.winner_id:
                print(f"Winner: {game_state.winner_id}")
            else:
                print("Game ended in a draw or unusual state.")
            break

    print("\n--- Game Finished ---")


if __name__ == "__main__":
    run_game()