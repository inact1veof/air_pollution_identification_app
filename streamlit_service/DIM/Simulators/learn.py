import pandas as pd
import numpy as np


def generate_learn_df(lines_count, isa_count, filename, path):
    data = []
    for _ in range(lines_count):
        row = {
            'K1': np.random.uniform(0, 1.5),
            'K2': np.random.uniform(0, 1.5),
            'K3': np.random.uniform(0, 1.5),
            'K4': np.random.uniform(0, 1.5),
            'K5': np.random.uniform(0, 1.5),
            'K6': np.random.uniform(0, 1.5),
            'K7': np.random.uniform(0, 1.5),
            'K8': np.random.uniform(0, 1.5),
            'WindDirection': np.random.uniform(1, 8),
            'WindSpeed': np.random.uniform(1, 15),
            'Temperature': np.random.uniform(-20, 20),
            'Humidity': np.random.uniform(0, 100),
        }
        col_num = 13
        isa_numbers = []
        for j in range(0, isa_count):
            isa_numbers.append(str(col_num))
            col_number = str(col_num)
            row[col_number] = 0
            col_num = col_num + 1
        num_isa = np.random.randint(1, isa_count)
        isa_columns = np.random.choice(isa_numbers, num_isa, replace=False)
        for col in isa_columns:
            row[col] = 100

        data.append(row)

    df = pd.DataFrame(data)

    df[['K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'WindDirection', 'WindSpeed', 'Temperature', 'Humidity']] = df[
        ['K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'WindDirection', 'WindSpeed', 'Temperature', 'Humidity']].astype(float)
    df.to_csv(f'{path}/{filename}_q_learn_df.csv', index=False)