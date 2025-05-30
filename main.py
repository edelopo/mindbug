from src.core.game_engine import GameEngine
from src.models.game_state import GameState
from src.agents.human_agent import HumanAgent
from src.utils.data_loader import load_cards_from_json, load_definitions_from_json
import os

def run_game():
    # 1. Load card definitions
    # Adjust the path to cards.json based on where main.py is relative to data/
    # Assuming main.py is in the project root, and cards.json is in data/
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    
    all_cards_list = load_cards_from_json(filepath=cards_json_path)
    card_definitions_dict = load_definitions_from_json(filepath=cards_json_path)

    # 2. Initialize Game Engine
    game_engine = GameEngine(card_definitions=card_definitions_dict)

    # 3. Initialize Game State
    player1_id = "Human Player 1"
    player2_id = "Human Player 2"
    game_state = GameState.initial_state(player1_id, player2_id, all_cards_list)

    # 4. Initialize Agents
    human_agent1 = HumanAgent(player1_id)
    human_agent2 = HumanAgent(player2_id)
    agents = {player1_id: human_agent1, player2_id: human_agent2}

    print("--- Starting Mindbug Game ---")
    
    # Game Loop
    while not game_state.game_over:
        active_player_id = game_state.active_player_id
        active_agent = agents[active_player_id]

        print(f"\n--- Turn {game_state.turn_count} ---")

        # Automatically handle draw phase transition, if your engine does it
        # Otherwise, the human agent would need to explicitly "draw" or "proceed"
        if game_state.phase == "draw_phase":
            # Assuming initial_state sets up hand, and game_engine handles subsequent draws on PlayCardAction
            # If draw phase implies a player action, you'd handle it here.
            # For simplicity, we assume engine transitions to play_phase after initial draw.
            print(f"{active_player_id} is in Draw Phase. (Cards dealt automatically)")
            # You might want to explicitly set phase to "play_phase" if your engine doesn't do it
            # game_state.phase = "play_phase" # Or the engine's start_turn method handles this

        # Get possible actions for the active player in the current phase
        possible_actions = game_engine.get_possible_actions(game_state)
        
        if not possible_actions and not game_state.game_over:
            print(f"{active_player_id} has no valid actions and loses!")
            game_state.game_over = True
            game_state.winner_id = game_state.inactive_player_id
            break

        # Human agent chooses an action
        chosen_action = active_agent.choose_action(game_state, possible_actions)

        # Apply the chosen action
        game_state = game_engine.apply_action(game_state, chosen_action)

        # Handle phase transitions or turn ending
        # The game_engine.apply_action already handles many phase transitions.
        # If the chosen action was an EndTurnAction, or if the current phase
        # should lead to the next player's turn, trigger the switch.
        if isinstance(chosen_action, EndTurnAction):
            print(f"{active_player_id} ends their turn.")
            game_state.switch_active_player()
            game_state.turn_count += 1
            game_state.phase = "play_phase" # Reset phase for next player

        # Check for game over conditions after each action
        if game_state.game_over:
            print(f"\n--- Game Over! ---")
            if game_state.winner_id:
                print(f"Winner: {game_state.winner_id}")
            else:
                print("Game ended in a draw or unusual state.") # Or define specific loss conditions
            break

    print("\n--- Game Finished ---")


if __name__ == "__main__":
    run_game()