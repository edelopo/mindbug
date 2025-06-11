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

    deck_size = 10
    hand_size = 5

    player1_id = "Human Player 1"
    player2_id = "Human Player 2"
    agents: Dict[str, BaseAgent] = {player1_id: HumanAgent(player1_id), player2_id: HumanAgent(player2_id)}

    game_engine = GameEngine(all_cards=all_cards_list, deck_size=deck_size, hand_size=hand_size, agents=agents)

    print("--- Starting Mindbug Game ---")
    
    game_engine.play_game(
        p1_forced_card_ids=['ferret_bomber'],
        p2_forced_card_ids=[]
    )

    print("\n--- Game Finished ---")
    # print(f"Winner: {game_state.winner_id}")

def run_pvai_game():
    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    all_cards_list = load_cards_from_json(filepath=cards_json_path)

    player1_id = "Human Player"
    player2_id = "AI Player"
    agents: Dict[str, BaseAgent] = {player1_id: HumanAgent(player1_id), player2_id: RandomAgent(player2_id)}

    game_engine = GameEngine(all_cards=all_cards_list, deck_size=10, hand_size=5, agents=agents)

    print("--- Starting Mindbug Game ---")
    
    game_engine.play_game(
        p1_forced_card_ids=[],
        p2_forced_card_ids=[]
    )

    print("\n--- Game Finished ---")
    # print(f"Winner: {game_state.winner_id}")

def run_aivai_game(deck_size: int = 5, hand_size: int = 2):
    # # Suppress prints for AI vs AI games
    # sys.stdout = open(os.devnull, 'w')
    # sys.stderr = open(os.devnull, 'w')

    current_dir = os.path.dirname(__file__)
    cards_json_path = os.path.join(current_dir, 'data', 'cards.json')
    all_cards_list = load_cards_from_json(filepath=cards_json_path)

    player1_id = "Random Agent"
    player2_id = "Zero Agent"
    agents: Dict[str, BaseAgent] = {player1_id: RandomAgent(player1_id), player2_id: ZeroAgent(player2_id)}

    game_engine = GameEngine(all_cards=all_cards_list, deck_size=deck_size, hand_size=hand_size, agents=agents)
    
    game_engine.play_game(
        p1_forced_card_ids=[],
        p2_forced_card_ids=[]
    )

if __name__ == "__main__":
    run_pvp_game()

    # ----------------------
    # Uncomment the following lines to run AI vs AI games in parallel
    # ----------------------

    # num_games = 100
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