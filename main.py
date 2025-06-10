# main.py (no significant changes needed here, as HumanAgent now uses CLI)
from src.core.game_engine import GameEngine
from src.models.game_state import GameState
from src.agents.base_agent import BaseAgent
from src.agents.human_agent import HumanAgent
from src.agents.random_agent import RandomAgent, ZeroAgent
from typing import Dict, List
from src.models.card import Card
from src.utils.data_loader import load_cards_from_json
import os, sys, traceback
import multiprocessing as mp
from itertools import repeat

def run_pvp_game():
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    
    all_cards_list = load_cards_from_json(filepath=cards_json_path)
    # Make a list of forced cards for testing purposes
    # forced_cards_1 = [card for card in all_cards_list if (
    #     card.id == 'snail_thrower'
    #     or card.id == 'urchin_hurler'
    # )]
    # forced_cards_2 = [card for card in all_cards_list if (
    #     card.id == 'lone_yeti'
    #     # or card.id == 'chameleon_sniper'
    # )]

    deck_size = 10
    hand_size = 5

    player1_id = "Human Player 1"
    player2_id = "Human Player 2"
    agents: Dict[str, BaseAgent] = {player1_id: HumanAgent(player1_id), player2_id: HumanAgent(player2_id)}
    game_state = GameState.initial_state(player1_id, player2_id, all_cards_list,
                                         deck_size=deck_size, hand_size=hand_size, 
                                        #  forced_cards_1=forced_cards_1,
                                        #  forced_cards_2=forced_cards_2
                                         )
    game_engine = GameEngine(deck_size=deck_size, hand_size=hand_size, agents=agents)

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

def run_pvai_game():
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    all_cards_list = load_cards_from_json(filepath=cards_json_path)
    # Make a list of forced cards for testing purposes
    # forced_cards_1 = [card for card in all_cards_list if (card.id == 'harpy_mother' or 
    #                                                     card.id == 'compost_dragon')]
    # forced_cards_2 = [card for card in all_cards_list if (card.id == 'axolotl_healer')]

    player1_id = "Human Player"
    player2_id = "AI Player"
    agents: Dict[str, BaseAgent] = {player1_id: HumanAgent(player1_id), player2_id: RandomAgent(player2_id)}
    game_state = GameState.initial_state(player1_id, player2_id, all_cards_list,
                                         deck_size=10, hand_size=5, 
                                        #  forced_cards_1=forced_cards_1,
                                        #  forced_cards_2=forced_cards_2
                                         )
    game_engine = GameEngine(deck_size=10, hand_size=5, agents=agents)

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

def run_aivai_game(deck_size: int = 5, hand_size: int = 2) -> GameState:
    # # Suppress prints for AI vs AI games
    # sys.stdout = open(os.devnull, 'w')
    # sys.stderr = open(os.devnull, 'w')

    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    all_cards_list = load_cards_from_json(filepath=cards_json_path)
    # Make a list of forced cards for testing purposes
    forced_cards_1 = [card for card in all_cards_list if (
        card.id == 'shark_dog'
        or card.id == 'snail_hydra'
    )]
    forced_cards_2 = [card for card in all_cards_list if (
        card.id == 'explosive_toad'
        or card.id == 'shield_bug'
    )]

    player1_id = "Random Agent"
    player2_id = "Zero Agent"
    agents: Dict[str, BaseAgent] = {player1_id: RandomAgent(player1_id), player2_id: ZeroAgent(player2_id)}
    game_state = GameState.initial_state(player1_id, player2_id, all_cards_list,
                                        deck_size, hand_size, 
                                        forced_cards_1=forced_cards_1,
                                        forced_cards_2=forced_cards_2
                                        )
    game_engine = GameEngine(deck_size, hand_size, agents=agents)
    
    while not game_state.game_over:
        active_player_id = game_state.active_player_id
        active_agent = agents[active_player_id]

        valid_actions = game_engine.get_valid_actions(game_state)
        
        if not valid_actions:
            # print(f"{active_player_id} has no valid actions and loses!")
            game_state.game_over = True
            game_state.winner_id = game_state.inactive_player_id
            break

        chosen_action = active_agent.choose_action(game_state, valid_actions)
        game_state = game_engine.apply_action(game_state, chosen_action)

    # print("\n--- Game Finished ---")
    # print(f"Winner: {game_state.winner_id}")
    if not game_state.winner_id:
        raise ValueError("Game ended without a winner.")
    return game_state


if __name__ == "__main__":
    run_pvai_game()

    # ----------------------
    # Uncomment the following lines to run AI vs AI games in parallel
    # ----------------------

    # num_games = 1000
    # deck_size = 10
    # hand_size = 5
    # args_list = [(deck_size, hand_size) for _ in range(num_games)]

    # # Run the games in parallel using multiprocessing
    # with mp.Pool() as pool:
    #     results = pool.starmap(run_aivai_game, args_list)

    # # # Run the games sequentially for debugging
    # # results = [run_aivai_game(deck_size, hand_size) for _ in range(num_games)]

    # # Re-enable prints
    # sys.stdout = sys.__stdout__
    # sys.stderr = sys.__stderr__
    # print(f"--- Completed {num_games} AI vs AI games ---")
    
    # # Count wins for each player
    # winners = [game_state.winner_id for game_state in results]
    # player1_wins = winners.count("Random Agent")
    # player2_wins = winners.count("Zero Agent")

    # print(f"Random Agent wins: {player1_wins} ({player1_wins/num_games:.1%})")
    # print(f"Zero Agent wins: {player2_wins} ({player2_wins/num_games:.1%})")