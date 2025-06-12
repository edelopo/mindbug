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
import json
import os
from datetime import datetime

def run_pvp_game():
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    all_cards_list = load_cards_from_json(filepath=cards_json_path)

    deck_size = 10
    hand_size = 5

    player1_id = "Human Player 1"
    player2_id = "Human Player 2"
    agents: Dict[str, BaseAgent] = {player1_id: HumanAgent(player1_id), player2_id: HumanAgent(player2_id)}

    game_engine = GameEngine(all_cards=all_cards_list, deck_size=deck_size, hand_size=hand_size, agents=agents)

    print("--- Starting Mindbug Game ---")
    
    logs = game_engine.play_game(
        p1_forced_card_ids=["ferret_bomber","tusked_extorter"],
        p2_forced_card_ids=[]
    )

    print("\n--- Game Finished ---")
    
    return logs

def run_pvai_game():
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    all_cards_list = load_cards_from_json(filepath=cards_json_path)

    player1_id = "Human Player"
    player2_id = "AI Player"
    agents: Dict[str, BaseAgent] = {player1_id: HumanAgent(player1_id), player2_id: RandomAgent(player2_id)}

    game_engine = GameEngine(all_cards=all_cards_list, deck_size=10, hand_size=5, agents=agents)

    print("--- Starting Mindbug Game ---")
    
    logs = game_engine.play_game(
        p1_forced_card_ids=[],
        p2_forced_card_ids=[]
    )

    print("\n--- Game Finished ---")
    
    return logs

def run_aivai_game(deck_size: int = 5, hand_size: int = 2):
    # Suppress prints for AI vs AI games
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    all_cards_list = load_cards_from_json(filepath=cards_json_path)

    player1_id = "AI1"
    player2_id = "AI2"
    agents: Dict[str, BaseAgent] = {player1_id: RandomAgent(player1_id), player2_id: ZeroAgent(player2_id)}

    game_engine = GameEngine(all_cards=all_cards_list, deck_size=deck_size, hand_size=hand_size, agents=agents)
    
    logs = game_engine.play_game(
        p1_forced_card_ids=[],
        p2_forced_card_ids=[]
    )

    return logs

if __name__ == "__main__":
    # ----------------------
    # Uncomment the following lines to run a Player vs Player game
    # ----------------------
    run_pvp_game()

    # ----------------------
    # Uncomment the following lines to run a Player vs AI game and record the logs
    # ----------------------
    # logs = run_pvai_game()
    # # Create a timestamp for the filename
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # filename = f"game_log_{timestamp}.json"

    # # Ensure the data/game_database directory exists
    # database_dir = os.path.join(os.path.dirname(__file__), 'data', 'game_database')
    # os.makedirs(database_dir, exist_ok=True)

    # # Write logs to the JSON file
    # filepath = os.path.join(database_dir, filename)
    # with open(filepath, 'w') as f:
    #     json.dump(logs, f, indent=2)

    # print(f"Game log saved to {filepath}")

    # ----------------------
    # Uncomment the following lines to run AI vs AI games in parallel
    # ----------------------

    # num_games = 100
    # deck_size = 10
    # hand_size = 5
    # args_list = [(deck_size, hand_size) for _ in range(num_games)]

    # # Run the games in parallel using multiprocessing
    # with mp.Pool() as pool:
    #     results_log = pool.starmap(run_aivai_game, args_list)

    # # # Run the games sequentially for debugging
    # # results = [run_aivai_game(deck_size, hand_size) for _ in range(num_games)]

    # # Re-enable prints
    # sys.stdout = sys.__stdout__
    # sys.stderr = sys.__stderr__
    # print(f"--- Completed {num_games} AI vs AI games ---")

    # # import pprint
    # # pprint.pp(results_log, width=120)
    
    # # Count wins for each player
    # winners = [log["final_state"]["winner_id"] for log in results_log]
    # player1_wins = winners.count("AI1")
    # player2_wins = winners.count("AI2")

    # print(f"Random Agent wins: {player1_wins} ({player1_wins/num_games:.1%})")
    # print(f"Zero Agent wins: {player2_wins} ({player2_wins/num_games:.1%})")

    # # Count win conditions
    # win_conditions = [log["final_state"]["win_condition"] for log in results_log]
    # run_out_of_actions_wins = win_conditions.count("run_out_of_actions")
    # life_below_zero_wins = win_conditions.count("life_below_zero")

    # print(f"Run out of actions wins: {run_out_of_actions_wins} ({run_out_of_actions_wins/num_games:.1%})")
    # print(f"Life below zero wins: {life_below_zero_wins} ({life_below_zero_wins/num_games:.1%})")