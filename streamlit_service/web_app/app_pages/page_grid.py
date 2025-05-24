import streamlit as st
import configparser
import folium
from streamlit_folium import folium_static
import os
import sys
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(parent_dir)

from DIM.parsers import get_isa_coords, get_analyzers_coords

def get_page():
    st.title("Карта среды идентификации")

    config = configparser.ConfigParser()
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    config.read(app_dir + '/config.ini')

    grid_start_point = (float(config['grid']['left_bottom_corner_lat']), float(config['grid']['left_bottom_corner_lon']))

    cell_size_lat = float(config['grid']['cell_size_lat'])
    cell_size_lon = float(config['grid']['cell_size_lon'])

    number_grid_size_l_size = int(config['grid']['l_size'])
    number_grid_size_h_size = int(config['grid']['h_size'])

    map_center = (config['grid']['map_center_lat'], config['grid']['map_center_lon'])

    m = folium.Map(location=map_center, zoom_start=12.5)

    xllcorner = -13000
    yllcorner = -4600
    cellsize = 200
    grid_width = 130
    grid_height = 101

    file_path_point = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + config['data']['isa_point_pos_filename']
    file_path_square = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + config['data']['isa_square_pos_filename']
    file_path_analyzers = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + config['data']['analyzers_pos_filename']

    isa_coords = get_isa_coords(file_path_point, file_path_square, grid_width, grid_height, xllcorner, yllcorner, cellsize)
    analyzers_coords = get_analyzers_coords(file_path_analyzers, grid_width, grid_height, xllcorner, yllcorner, cellsize)

    isa_coords.to_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + "system_isa_coords.csv")
    analyzers_coords.to_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + "system_analyzer_coords.csv")

    for i in range(number_grid_size_h_size):
        for j in range(number_grid_size_l_size):
            lat1 = grid_start_point[0] - cell_size_lat / 2 + i * cell_size_lat
            lon1 = grid_start_point[1] - cell_size_lon / 2 + j * cell_size_lon
            lat2 = lat1 + cell_size_lat
            lon2 = lon1 + cell_size_lon

            cell_color = 'grey'
            flag_isa = 0
            for index, row in isa_coords.iterrows():
                if i == row['y'] and j == row['x']:
                    polygon = folium.Polygon(
                        locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                        color='red',
                        fill=True,
                        fill_opacity=0.5,
                        border=0.05,
                        popup=row['Name'],
                    )
                    m.add_child(polygon)
                    flag_isa = 1
                    continue
            flag_analyzer = 0
            for index, row in analyzers_coords.iterrows():
                if i == row['y'] and j == row['x']:
                    polygon = folium.Polygon(
                        locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                        color='blue',
                        fill=True,
                        fill_opacity=0.5,
                        border=0.05,
                        popup=row['Name'],
                    )
                    m.add_child(polygon)
                    flag_analyzer = 1
                    continue
            if flag_isa == 0 and flag_analyzer == 0:
                polygon = folium.Polygon(
                    locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                    color=cell_color,
                    fill=True,
                    fill_opacity=0.05,
                    border=0.1,
                )
                if cell_color == 'red' or cell_color == 'blue':
                    polygon.options['weight'] = 0.2
                if cell_color == 'grey':
                    polygon.options['weight'] = 0.4

                m.add_child(polygon)

    folium_static(m, width=1300, height=700)