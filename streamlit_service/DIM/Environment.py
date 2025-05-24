import math
import pandas as pd
import numpy as np


class Environment:
    def __init__(self, max_x, max_y):
        self.max_x = max_x
        self.max_y = max_y

    def step(self, state, action, target_position):
        next_state = state.copy()
        if action == 'Up':
            if next_state['PositionY'] < self.max_y:
                next_state['PositionY'] = state['PositionY'] + 1
        elif action == 'Down':
            if next_state['PositionY'] > 0:
                next_state['PositionY'] = state['PositionY'] - 1
        elif action == 'Left':
            if next_state['PositionX'] > 0:
                next_state['PositionX'] = state['PositionX'] - 1
        elif action == 'Right':
            if next_state['PositionX'] < self.max_x:
                next_state['PositionX'] = state['PositionX'] + 1

        agent_position = [next_state['PositionX'], next_state['PositionY']]

        done = False
        if agent_position == target_position:
            done = True

        return next_state, done

    def calc_reward(self, state, action, target_position):
        agent_position = [0, 0]
        if action == 'Up':
            if state['PositionY'] < self.max_y:
                agent_position = [state['PositionX'], state['PositionY'] + 1]
        elif action == 'Down':
            if state['PositionY'] > 0:
                agent_position = [state['PositionX'], state['PositionY'] - 1]
        elif action == 'Left':
            if state['PositionX'] > 0:
                agent_position = [state['PositionX'] - 1, state['PositionY']]
        elif action == 'Right':
            if state['PositionX'] < self.max_x:
                agent_position = [state['PositionX'] + 1, state['PositionY']]

        if agent_position == [0, 0]:
            return 0

        try:
            distance = 1 / (
                math.sqrt((target_position[0] - agent_position[0]) ** 2 + (target_position[1] - agent_position[1]) ** 2))
        except:
            distance = 1.1
        return distance
