import numpy as np
import pandas as pd


class QLearningAgent:
    def __init__(self, actions, target_pos, learning_rate=0.1, discount_factor=0.9, exploration_prob=0.2):
        self.actions = actions
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_prob = exploration_prob
        self.q_states = pd.DataFrame(
            columns=['PositionX', 'PositionY', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'WindDirection',
                     'WindSpeed', 'Temperature', 'Humidity'], dtype=float)
        self.q_actions = pd.DataFrame(
            columns=['Q_Up', 'Q_Down', 'Q_Left', 'Q_Right'], dtype=float)
        self.target_position = target_pos

    def get_action_q(self, state, env):
        actions = ['Up', 'Down', 'Left', 'Right']
        actions_rewards = [0, 0, 0, 0]

        for i in range(0, len(actions_rewards)):
            actions_rewards[i] = env.calc_reward(state, actions[i], self.target_position)

        return actions, actions_rewards

    def calc_q_with_reward(self, state, action, reward_value):
        if tuple(state) not in self.q_states:
            q_value = 0
        else:
            index = self.q_states.index(state)
            action_name = f'Q_' + action
            q_value = self.q_actions[index, action_name]

        return q_value + self.learning_rate * (reward_value + self.discount_factor * reward_value - q_value)

    def update_q_table(self, state, actions, rewards, env):
        action_rewards_final = {'Q_Up': self.calc_q_with_reward(state, actions[0], rewards[0]),
                                'Q_Down': self.calc_q_with_reward(state, actions[1], rewards[1]),
                                'Q_Left': self.calc_q_with_reward(state, actions[2], rewards[2]),
                                'Q_Right': self.calc_q_with_reward(state, actions[3], rewards[3])}
        self.q_states = self.q_states._append(state, ignore_index=True)
        self.q_actions = self.q_actions._append(action_rewards_final, ignore_index=True)

        next_state, done = env.step(state, actions[np.argmax(np.array(rewards))], self.target_position)
        best_q = action_rewards_final[f'Q_{actions[np.argmax(np.array(rewards))]}']
        return next_state, done, best_q

    def set_exploration_prob(self, exploration_prob):
        self.exploration_prob = exploration_prob
