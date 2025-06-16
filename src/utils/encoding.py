from src.models.game_state import GameState
import numpy as np

ENCODING_INDEX = {
    'axolotl_healer': 1,
    'bee_bear': 2,
    'brain_fly': 3,
    'chameleon_sniper': 4,
    'compost_dragon': 5,
    'deathweaver': 6,
    'elephantopus': 7,
    'explosive_toad': 8,
    'ferret_bomber': 9,
    'giraffodile': 10,
    'goblin_werewolf': 11,
    'gorillion': 12,
    'grave_robber': 13,
    'harpy_mother': 14,
    'kangasaurus_rex': 15,
    'killer_bee': 16,
    'lone_yeti': 17,
    'luchataur': 18,
    'mysterious_mermaid': 19,
    'plated_scorpion': 20,
    'rhyno_turtle': 21,
    'shark_dog': 22,
    'sharky_crab-dog-mummypus': 23,
    'shield_bugs': 24,
    'snail_hydra': 25,
    'snail_thrower': 26,
    'spider_owl': 27,
    'strange_barrel': 28,
    'tiger_squirrel': 29,
    'turbo_bug': 30,
    'tusked_extorter': 31,
    'urchin_hurler': 32
}

def encode_game_state(game_state: GameState) -> np.ndarray:
    """
    Encodes the game state into a feature vector. The feature vector includes:
    - Current turn
    For each player:
    - Life points
    - Mindbugs remaining
    - Cards left in deck
    - Number of cards in hand
    - List of cards in hand according to their encoding index (always size 7, padded with zeros if necessary)
    - Number of cards in play area
    - List of cards in play area according to their encoding index (always size 7)
    - Number of cards in discard pile
    - List of cards in discard pile according to their encoding index (always size 10)

    The size of the feature vector is fixed at 61.
    """
    features = []
    player = game_state.get_active_player()
    opponent = game_state.get_inactive_player()

    features.append(game_state.turn_count)
    
    features.append(player.life_points)
    features.append(player.mindbugs)
    features.append(len(player.deck))  # Cards left in deck
    # Encode player's hand
    features.append(len(player.hand))
    player_hand_encoding = [ENCODING_INDEX[card.id] for card in player.hand]
    player_hand_encoding += [0] * (7 - len(player_hand_encoding))  # Pad to size 7
    features.extend(player_hand_encoding[:7])  # Ensure only the first 7 cards are included
    # Encode player's play area
    features.append(len(player.play_area))
    player_play_area_encoding = []
    for card in player.play_area:
        index = ENCODING_INDEX[card.id]
        if card.is_exhausted:
            index = -index  # Use negative index for exhausted cards
    player_play_area_encoding += [0] * (7 - len(player_play_area_encoding))  # Pad to size 7
    features.extend(player_play_area_encoding[:7])  # Ensure only the first 7 cards are included
    # Encode player's discard pile
    features.append(len(player.discard_pile))
    player_discard_encoding = [ENCODING_INDEX[card.id] for card in player.discard_pile]
    player_discard_encoding += [0] * (10 - len(player_discard_encoding))  # Pad to size 10
    features.extend(player_discard_encoding[:10])  # Ensure only the first 10 cards are included
    
    features.append(opponent.life_points)
    features.append(opponent.mindbugs)
    features.append(len(opponent.deck))  # Cards left in deck
    # Encode opponent's hand
    features.append(len(opponent.hand))
    opponent_hand_encoding = [ENCODING_INDEX[card.id] for card in opponent.hand]
    opponent_hand_encoding += [0] * (7 - len(opponent_hand_encoding))  # Pad to size 7
    features.extend(opponent_hand_encoding[:7])  # Ensure only the first 7 cards are included
    # Encode opponent's play area
    features.append(len(opponent.play_area))
    opponent_play_area_encoding = []
    for card in opponent.play_area:
        index = ENCODING_INDEX[card.id]
        if card.is_exhausted:
            index = -index  # Use negative index for exhausted cards
    opponent_play_area_encoding += [0] * (7 - len(opponent_play_area_encoding))  # Pad to size 7
    features.extend(opponent_play_area_encoding[:7])  # Ensure only the first 7 cards are included
    # Encode opponent's discard pile
    features.append(len(opponent.discard_pile))
    opponent_discard_encoding = [ENCODING_INDEX[card.id] for card in opponent.discard_pile]
    opponent_discard_encoding += [0] * (10 - len(opponent_discard_encoding))  # Pad to size 10
    features.extend(opponent_discard_encoding[:10])  # Ensure only the first 10 cards are included

    return np.array(features, dtype=np.float32)