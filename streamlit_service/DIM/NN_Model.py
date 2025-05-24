import pandas as pd
import numpy as np
import os

from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import SGD

from sklearn.preprocessing import StandardScaler
from DIM.parsers import get_isa_point_coords, get_isa_name, get_analyzer_coords
from DIM.gral_methods import make_caclulation_list, run_normal
import tensorflow as tf

class NN_model:
    def __init__(self, num_par, calc_dir, isa_path, analyzer_path, indexes):
        NN_model = Sequential()
        NN_model.add(Dense(64, activation='relu', input_dim=num_par))
        NN_model.add(Dropout(0.5))
        NN_model.add(Dense(32, activation='relu'))
        NN_model.add(Dropout(0.5))
        NN_model.add(Dense(16, activation='relu'))
        NN_model.add(Dropout(0.5))
        NN_model.add(Dense(4, activation='softmax'))
        

        sgd = SGD(learning_rate=0.01, weight_decay=1e-6, momentum=0.9, nesterov=True)
        NN_model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

        self.model = NN_model
        self.n = None
        self._data_arr = None
        self._counter = 0
        self._calc_dir = calc_dir
        self._isa_path = isa_path
        self._analyzer_path = analyzer_path
        self._indexes = indexes

    @staticmethod
    def get_grid_data(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()

        grid_data = []
        for line in lines[6:]:
            grid_data.append([float(val) for val in line.split()])

        grid_data = np.array(grid_data)

        return grid_data

    @staticmethod
    def build_path(x1, y1, x2, y2):
        path = []
        current_x, current_y = x1, y1

        balanced = 1

        while current_x != x2 or current_y != y2:
            path.append((current_x, current_y))

            if current_x != x2 and current_y != y2:
                if balanced == 1:
                    current_x += 1 if current_x < x2 else -1
                    balanced = 0
                    continue
                if balanced == 0:
                    current_y += 1 if current_y < y2 else -1
                    balanced = 1
                    continue
            elif current_x == x2:
                current_y += 1 if current_y < y2 else -1
            elif current_y == y2:
                current_x += 1 if current_x < x2 else -1

        path.append((x2, y2))

        return path


    def get_data(self, analyzer_coords):
        run_normal()

        directory = self._calc_dir

        folder_names = ['01_source', '04_source', '05_source', '06_source', '07_source', '08_source', '09_source',
                        '10_source', '11_source', '12_source', '13_source', '14_source']

        sum = 1.5
        dir = directory + '00_normal/'

        file_names = os.listdir(dir)
        for file in file_names:
            path = dir + file
            data = self.get_grid_data(path)
            data = data[::-1, :]
            sum += data[48, 39]

        self.n = (self._exideed_value / sum)

        make_caclulation_list(self.n)

        result = []

        for folder in folder_names:
            dir = directory + folder + '/'
            file_names = os.listdir(dir)
            for file in file_names:
                path = dir + file
                data = self.get_grid_data(path)
                data = data[::-1, :]
                isa_index = file[-6:-4]
                i = analyzer_coords[0]
                j = analyzer_coords[1]
                subarray = data[i - 2:i + 3, j - 2:j + 3]
                item = {'folder': folder[:2], 'isa_index': isa_index, 'value_no4': np.max(subarray)}
                result.append(item)

        df_res = pd.DataFrame(result, columns=['folder', 'isa_index', 'value_no4'])
        pivot_df = df_res.pivot(index='isa_index', columns='folder', values='value_no4')
        pivot_df['Фон'] = 1.5
        pivot_df['sum'] = pivot_df.sum(axis=1)

        all_sum = pivot_df['sum'].sum()

        pivot_df['Вклад (%)'] = (pivot_df['sum'] / all_sum) * 100
        self._data_arr = pivot_df

    def get_pos(self, analyzer_coords):
        max_index = self._data_arr['Вклад (%)'].idxmax()
        max_index = str(int(max_index))
        isa_coord_x, isa_coord_y = get_isa_point_coords(get_isa_name(max_index, self._indexes), self._isa_path)
        start_x = analyzer_coords[0]
        start_y = analyzer_coords[1]
        result = self.build_path(start_x,start_y,isa_coord_x, isa_coord_y)
        return result

    def fit(self, X_train, y_train, analyzer_name):
        analyzer_coords = get_analyzer_coords(analyzer_name, self._analyzer_path)
        self.get_data(analyzer_coords)
        pos = self.get_pos(analyzer_coords)
        self._pos = pos
        self.model.fit(X_train, y_train, epochs=1000, batch_size=32, validation_split=0.2)

    def predict(self, X, sensors_data):
        if self._counter < len(self._pos) - 1:
            res = self._pos[self._counter]
            self._counter += 1
        else:
            res = None
        return res
        self.model.predict(X)
