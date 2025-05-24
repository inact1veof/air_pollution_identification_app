import time

import streamlit as st
import configparser
import folium
from streamlit_folium import folium_static
import os
import sys
import pandas as pd
import random
import pandas as pd
import numpy as np
from datetime import datetime

from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import SGD

from sklearn.preprocessing import StandardScaler

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(parent_dir)

from DIM.parsers import get_isa_coords, get_analyzers_coords
from DIM.Agent import QLearningAgent
from DIM.Environment import Environment
from DIM.NN_Model import NN_model

class StreamToLogger(object):
    def __init__(self, text_area, max_lines=40):
        self.text_area = text_area
        self.logs = ""
        self.max_lines = max_lines

    def write(self, message):
        self.logs = message + self.logs
        log_lines = self.logs.splitlines()
        if len(log_lines) > self.max_lines:
            self.logs = "\n".join(log_lines[:self.max_lines])
        self.text_area.text(self.logs)

    def flush(self):
        pass

def get_page():
    st.title("Обучение модели идентификации")

    config = configparser.ConfigParser()
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    config.read(app_dir + '/config.ini')


    col1, col2, col3 = st.columns([3, 0.1, 1])

    col2.write(
        """
        <style>
        .vertical-line {
            border-left: 2px solid gray;
            height: 1000px;
            position: absolute;
            left: -5%;
        }
        </style>
        <div class="vertical-line"></div>
        """,
        unsafe_allow_html=True
    )

    number_grid_size_l_size = int(config['grid']['l_size'])
    number_grid_size_h_size = int(config['grid']['h_size'])
    learn_filename = config['data']['learn_dataframe_filename']

    with col3:
        st.header("Информация")
        st.markdown(
            f"""
                <style>
                .styled-select {{
                    display: block;
                    width: 100%;
                    padding: 15px;
                    font-size: 16px;
                    line-height: 1.4;
                    color: #555;
                    background: #fff;
                    border: 1px solid #ccc;
                    border-radius: 10px;
                    -webkit-appearance: none;
                    -moz-appearance: none;
                    appearance: none;
                }}
                </style>

                <div style="width: 370px; height: 150px; background-color: lightgray; border-radius: 10px; padding: 20px; margin-bottom: 15px;">
                    <h5>Размер сетки: {number_grid_size_l_size}x{number_grid_size_h_size}</h5>
                    <h5><u>Файл обучающего датасета:</u></h5> 
                        <h6>{learn_filename}</h6>
                </div>
                """,
            unsafe_allow_html=True
        )
        st.markdown("""
                    <style>
                    .stButton>button {
                        width: 370px; /* Ширина кнопок */
                        height: 50px; /* Высота кнопок */
                        color: white; /* Белый текст */
                        border: none; /* Без границы */
                        border-radius: 5px; /* Закругленные углы */
                        cursor: pointer; /* Указатель мыши при наведении */
                        font-size: 16px; /* Размер шрифта */
                        margin-right: 10px; /* Отступ между кнопками */
                        transition: background-color 0.6s; /* Плавный переход цвета фона */
                        background-color: #9e9e9e; /* Светло-серый цвет */
                    }

                    /* Стиль для кнопки "Начать обучение" */
                    .stButton>button:nth-of-type(1) {
                        background-color: #9e9e9e; /* Светло-серый цвет */
                    }

                    .stButton>button:hover {
                        background-color: #757575; /* Темно-серый цвет при наведении */
                        color: white; /* Оставить текст белым при наведении */
                        opacity: 0.99; /* Плавное изменение при наведении */
                    }
                    </style>
                """, unsafe_allow_html=True)

        start_button = st.button("Начать обучение")
        stop_button = st.button("Прервать обучение")

    with col1:
        st.write('Процесс обучения модели')

        if 'logs' not in st.session_state:
            st.session_state.logs = ""

        log_box = st.empty()

        if start_button:
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
            learn_set_name = config['data']['learn_dataframe_filename']
            # data
            df = pd.read_csv(data_dir + learn_set_name)
            df_cases = df[['K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'WindDirection', 'WindSpeed', 'Temperature',
                           'Humidity']]
            df_pipes = df[['13', '14', '15', '16', '17']]

            pipes_coords = [[7, 8], [7, 10], [9, 7], [10, 7], [11, 9]]
            analyzers_coords = [[2, 9], [3, 14], [4, 4], [9, 3], [9, 16], [14, 5], [14, 14], [16, 9]]

            # Параметры
            actions = ['Up', 'Down', 'Left', 'Right']

            # Инициализация агента и среды
            agent = QLearningAgent(actions, [0, 0])
            env = Environment(101, 131)

            # Форматирование данных для агента
            df_learn_cases = pd.DataFrame(
                columns=['PositionX', 'PositionY', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'WindDirection',
                         'WindSpeed', 'Temperature', 'Humidity'])
            counter = 0
            for str_item in df_cases.values:
                if counter % 100 == 0:
                    st.session_state.logs = f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Обрабатывается {counter}/{len(df_cases.values)} ситуация идентификации\n" + st.session_state.logs
                    log_box.text_area("Процесс обучения:", value=st.session_state.logs, height=800, disabled=True)
                max_pollution = str_item[[0, 1, 2, 3, 4, 5, 6, 7]]
                max_index = np.argmax(max_pollution)
                agent_coords = analyzers_coords[int(max_index) - 1]

                app_item = {'PositionX': agent_coords[0], 'PositionY': agent_coords[1], 'K1': str_item[0],
                            'K2': str_item[1], 'K3': str_item[2], 'K4': str_item[3], 'K5': str_item[4],
                            'K6': str_item[5], 'K7': str_item[6], 'K8': str_item[7], 'WindDirection': str_item[8],
                            'WindSpeed': str_item[9], 'Temperature': str_item[10], 'Humidity': str_item[11]}
                df_learn_cases = df_learn_cases._append(app_item, ignore_index=True)
                counter += 1

            # Обучение агента
            num_episodes = len(df_cases)
            for episode in range(num_episodes):
                if episode % 100 == 0:
                    st.session_state.logs = f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Агент рассмотрел ситуацию {episode} из {num_episodes} \n" + st.session_state.logs
                    log_box.text_area("Процесс обучения:", value=st.session_state.logs, height=800, disabled=True)

                pipe_outs = np.array(df_pipes.loc[episode])

                agent.target_position = pipes_coords[np.argmax(pipe_outs)]

                state = df_learn_cases.loc[episode]
                done = False

                while not done:
                    actions, actions_rewards = agent.get_action_q(state, env)
                    state, done, best_q = agent.update_q_table(state, actions, actions_rewards, env)


            model = NN_model(14, '', '', '', '')

            X_train = np.array(agent.q_states)
            y_train = np.array(agent.q_actions)

            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)

            st.session_state.logs = f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Начало обучение нейронной сети \n" + st.session_state.logs

            logger = StreamToLogger(log_box)
            sys.stdout = logger

            model.model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2, verbose=2)
            sys.stdout = sys.__stdout__
            model_name = 'nn_model_sample.h5'
            model.model.save(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + model_name)
            st.session_state.logs = f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Конец обучение нейронной сети \n" + st.session_state.logs
            st.success(f"Обучение завершено. Модель сохранена как: {model_name}")


        if stop_button:
            st.session_state.running = False
            log_box.text_area("Логи процесса обучения:", value=st.session_state.logs, height=200, disabled=True)
            st.write("Процесс остановлен.")