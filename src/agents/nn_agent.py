from src.agents.base_agent import BaseAgent
from src.models.game_state import GameState
from src.models.action import Action, PlayCardAction
from src.utils.encoding import encode_game_state
from typing import List, Dict

import os
import torch
from torch import nn

class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(70, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 10), # We assume a maximum of 10 possible actions
        )

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits

class NeuralNetworkAgent(BaseAgent):
    def __init__(self, player_id: str, brain: NeuralNetwork):
        super().__init__(player_id)
        if torch.accelerator.is_available():
            accelerator = torch.accelerator.current_accelerator()
            if not accelerator:
                raise ValueError("No accelerator found. Please ensure you have a valid accelerator setup.")
            self.device = accelerator.type
        else:
            self.device = "cpu"
        self.brain = brain.to(self.device)
        self.brain.eval()  # Set the model to evaluation mode

    def choose_action(self, game_state: GameState, possible_actions: List[Dict[str, Action | str]]) -> Action:
        """
        Neural network agent chooses an action using its brain.
        """
        # Get the list of possible actions
        possible_action_list = [action['action'] for action in possible_actions]

        # Encode the game state
        encoded_state = torch.from_numpy(encode_game_state(game_state)).float().unsqueeze(0)  # Add batch dimension
        encoded_state = encoded_state.to(self.device)  # Move to the appropriate device
        # Get the logits from the neural network
        logits = self.brain(encoded_state)
        # Mask the logits to only consider possible actions
        if game_state._pending_action == 'play_or_attack':
            n_playable_cards = 0
            for action in possible_action_list:
                if isinstance(action, PlayCardAction):
                    n_playable_cards += 1
            n_attacker_cards = len(possible_action_list) - n_playable_cards
            # The first five parameters are for playable cards, the next five for attacker cards
            for i in range(n_playable_cards, 5):
                logits[0][i] = float('-inf')
            for i in range(5 + n_attacker_cards, 10):
                logits[0][i] = float('-inf')
        else:
            for i in range(len(possible_action_list), len(logits[0])):
                logits[0][i] = float('-inf')  # Set logits for impossible actions to -inf
        # Convert logits to probabilities
        probabilities = nn.Softmax(dim=1)(logits)

        # Choose an action based on the probabilities
        chosen_action_index = int(torch.multinomial(probabilities, num_samples=1).item())
        if game_state._pending_action == 'play_or_attack' and chosen_action_index >= 5:
            # It's an attacker card
            chosen_action = possible_action_list[chosen_action_index - 5]
        else:
            chosen_action = possible_action_list[chosen_action_index]
        
        if not isinstance(chosen_action, Action):
            raise ValueError(f"Chosen action is not an instance of Action: {chosen_action}")
        
        return chosen_action