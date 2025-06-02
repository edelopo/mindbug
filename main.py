# main.py (no significant changes needed here, as HumanAgent now uses CLI)
from src.core.game_engine import GameEngine
from src.models.game_state import GameState
from src.agents.human_agent import HumanAgent
from src.utils.data_loader import load_cards_from_json, load_definitions_from_json
import os

def run_game():
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    
    all_cards_list = load_cards_from_json(filepath=cards_json_path)
    # Make a list of forced cards for testing purposes
    forced_cards_1 = [card for card in all_cards_list if (card.id == 'harpy_mother' or 
                                                        card.id == 'compost_dragon')]
    forced_cards_2 = [card for card in all_cards_list if (card.id == 'axolotl_healer')]

    player1_id = "Human Player 1"
    player2_id = "Human Player 2"
    agents = {player1_id: HumanAgent(player1_id), player2_id: HumanAgent(player2_id)}
    game_state = GameState.initial_state(player1_id, player2_id, all_cards_list,
                                         deck_size=5, hand_size=2, 
                                         forced_cards_1=forced_cards_1,
                                         forced_cards_2=forced_cards_2
                                         )
    game_engine = GameEngine(deck_size=5, hand_size=2, agents=agents)

    print("--- Starting Mindbug Game ---")
    
    while not game_state.game_over:
        active_player_id = game_state.active_player_id
        active_agent = agents[active_player_id]

        valid_actions = game_engine.get_valid_actions(game_state)
        
        if not valid_actions:
            print(f"{active_player_id} has no valid actions and loses!")
            game_state.game_over = True
            game_state.winner_id = game_state.inactive_player_id
            break

        chosen_action = active_agent.choose_action(game_state, valid_actions)

        game_state = game_engine.apply_action(game_state, chosen_action)

    print("\n--- Game Finished ---")
    print(f"Winner: {game_state.winner_id}")


if __name__ == "__main__":
    run_game()