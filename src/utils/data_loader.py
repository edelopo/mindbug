import json
import os
import copy
from typing import List, Dict
from src.models.card import Card

def load_cards_from_json(filepath=None) -> List[Card]:
    """
    Loads cards from a JSON file and returns a list
    of Card objects, according to their 'amount'.
    """
    if filepath is None:
        # Construct the default path relative to the project root
        # This assumes the script is run from mindbug_ai/ or a sibling directory
        # For a script in mindbug_ai/, it would be 'data/cards.json'
        # For this temporary test script, we'll assume it's run from the root.
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        filepath = os.path.join(project_root, 'data', 'cards.json')

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Card data file not found at: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        card_data_list = json.load(f)

    cards = []
    for card_data in card_data_list:
        for _ in range(card_data.get('amount', 1)):
            # We need to create a new instance so that each card has a different UUID
            cards.append(copy.deepcopy(Card.from_dict(card_data)))
    return cards

def load_definitions_from_json(filepath=None) -> Dict[str, Card]:
    """
    Loads card definitions from a JSON file and returns a Dict
    of Card objects, indexed by their 'id'.
    """
    if filepath is None:
        # Construct the default path relative to the project root
        # This assumes the script is run from mindbug_ai/ or a sibling directory
        # For a script in mindbug_ai/, it would be 'data/cards.json'
        # For this temporary test script, we'll assume it's run from the root.
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        filepath = os.path.join(project_root, 'data', 'cards.json')

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Card data file not found at: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        card_data_list = json.load(f)

    cards = {}
    for card_data in card_data_list:
        card = Card.from_dict(card_data)
        cards[card_data.get('id')] = card
    return cards