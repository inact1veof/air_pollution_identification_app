import pandas as pd
import numpy as np
import os

def point_in_cell(x, y, cell_x, cell_y, cellsize):
    return (cell_x <= x < cell_x + cellsize) and (cell_y <= y < cell_y + cellsize)

def get_isa_coords(filepath_point, filepath_square, grid_width, grid_height, xllcorner, yllcorner, cellsize):
    data = []

    with open(filepath_point, 'r') as file:
        next(file)
        next(file)
        for line in file:
            values = line.strip().split(',')
            if len(values) >= 3:
                name = values[0]
                x = float(values[1])
                y = float(values[2])
                data.append([name, x, y])
    with open(filepath_square, 'r') as file:
        next(file)
        next(file)
        for line in file:
            values = line.strip().split(',')
            if len(values) >= 29:
                name = values[0]
                x = float(values[27])
                y = float(values[28])
                data.append([name, x, y])

    df = pd.DataFrame(data, columns=['Name', 'x', 'y'])

    data = []
    grid = np.zeros((grid_height, grid_width))

    for i in range(grid_width):
        for j in range(grid_height):
            cell_x = xllcorner + i * cellsize
            cell_y = yllcorner + j * cellsize

            for _, row in df.iterrows():
                if point_in_cell(row['x'], row['y'], cell_x, cell_y, cellsize):
                    grid[j, i] = grid[j, i] + 1
                    obj = {'Name': row['Name'], 'x': i, 'y': j}
                    data.append(obj)

    df_good = pd.DataFrame(data)

    return df_good


def get_analyzers_coords(filepath, grid_width, grid_height, xllcorner, yllcorner, cellsize):
    data = []
    with open(filepath, 'r') as file:
        for line in file:
            values = line.strip().split(',')
            if len(values) >= 3:
                name = values[4]
                x = float(values[1])
                y = float(values[2])
                data.append([name, x, y])
    df = pd.DataFrame(data, columns=['Name', 'x', 'y'])

    grid = np.zeros((grid_height, grid_width))
    data = []
    for i in range(grid_width):
        for j in range(grid_height):
            cell_x = xllcorner + i * cellsize
            cell_y = yllcorner + j * cellsize

            for _, row in df.iterrows():
                if point_in_cell(row['x'], row['y'], cell_x, cell_y, cellsize):
                    grid[j, i] = grid[j, i] + 1
                    obj = {'Name': row['Name'], 'x': i, 'y': j}
                    data.append(obj)

    df_good = pd.DataFrame(data)

    return df_good


def get_isa_name(idx, path):
    data = {}
    data_dir = path
    filename = 'Sourcegroups.txt'
    with open(data_dir + filename, 'r') as file:
        for line in file:
            values = line.strip().split(',')
            data[values[1]] = values[0]

    return data[idx]

def get_isa_point_coords(name, path):
    name = str(int(name))
    isa_coords = pd.read_csv(path)
    isa_coords['Name'] = isa_coords['Name'].astype(str)
    result = isa_coords.loc[isa_coords['Name'] == name, ['x', 'y']]
    x_value, y_value = result.values[0]
    return y_value, x_value

def get_analyzer_coords(name, path):
    analyzer_coords = pd.read_csv(path)
    analyzer_coords['Name'] = analyzer_coords['Name'].astype(str)
    result = analyzer_coords.loc[analyzer_coords['Name'] == name, ['x', 'y']]
    x_value, y_value = result.values[0]
    return y_value, x_value
