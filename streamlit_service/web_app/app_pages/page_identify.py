import time

import streamlit as st
import configparser
import folium
from streamlit_folium import folium_static
import os
import sys
import pandas as pd
import random

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(parent_dir)

from DIM.NN_Model import NN_model
from DIM.parsers import get_isa_name

def get_page():

    st.title("Идентификация")
    config = configparser.ConfigParser()
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    config.read(app_dir + '/config.ini')

    st.session_state['marker_position'] = (0, 0)
    st.session_state['history'] = []
    if 'expansions' not in st.session_state:
        st.session_state['expansions'] = {}

    if "predict" not in st.session_state:
        st.session_state["predict"] = False
        st.session_state['path'] = []

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
    predict_filename = config['data']['predict_dataframe_filename']

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

                    <div style="width: 400px; height: 150px; background-color: lightgray; border-radius: 10px; padding: 20px; margin-bottom: 15px;">
                        <h5><u>Размер сетки:</u> {number_grid_size_l_size}x{number_grid_size_h_size}</h5>
                        <h5><u>Файл датасета ситуаций:</u></h5> 
                            <h6>{predict_filename}</h6>
                        <br>
                    </div>
                    """,
            unsafe_allow_html=True
        )
        if st.button("Поиск превышений в файле"):
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
            input_data = pd.read_csv(data_dir + config['data']['predict_dataframe_filename'])

            for index, row in input_data.iterrows():
                row_data = row.iloc[2:-2]
                filtered_row = row_data[row_data > 1]
                max_column = filtered_row.idxmax() if not filtered_row.empty else None

                if max_column is not None:
                    esp_label = f"Превышение {row['date']} | {row['time']}"
                    if esp_label not in st.session_state['expansions']:
                        st.session_state['expansions'][esp_label] = {
                            'max_column': max_column,
                            'date': row['date'],
                            'time': row['time'],
                            'value': row[max_column],
                            'wind_speed': row['wind_speed'],
                            'wind_direction': row['wind_direction'],
                            'identification_done': False,
                            'identification_result': None,
                            'identification_result_one': None,
                            'analyzers_values': row_data,
                        }
        for esp_label, esp_data in st.session_state['expansions'].items():
            esp = st.expander(label=esp_label, expanded=False)
            with esp:
                st.write(f'Зафиксировано превышение на посте контроля {esp_data["max_column"]}')
                st.write(f'Дата: {esp_data["date"]} | Время: {esp_data["time"]}')
                st.write(f'Значение: {esp_data["value"]}')
                st.write(f'Показания ветра: скорость = {esp_data["wind_speed"]} м/c, направление: {esp_data["wind_direction"]}')

                if esp_data['identification_done']:
                    result_lines = "<br>".join(esp_data['identification_result'])
                    st.markdown(
                        f"""
                            <div style="background-color: #dff0d8; padding: 10px; border-radius: 5px; color: #3c763d;">
                                <strong>Идентификация завершена:</strong><br>
                                - Источник с наибольшим вкладом: <strong>{esp_data['identification_result_one']}</strong><br>
                                - Вклады источников:<br>
                                {result_lines}
                            </div>
                            """,
                        unsafe_allow_html=True
                    )
                else:
                    if st.button(f"Провести идентификацию {esp_label}"):
                        calc_path = os.path.abspath(
                            os.path.join(os.path.dirname(__file__), os.pardir)) + "/calculation_files/"
                        isa_coords = os.path.abspath(
                            os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + "system_isa_coords.csv"
                        analyzers_coords = os.path.abspath(
                            os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + "system_analyzer_coords.csv"
                        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"

                        model = NN_model(14, calc_path, isa_coords, analyzers_coords, data_dir, float(esp_data["value"]))
                        model.fit(0, 0, esp_data["max_column"])

                        path = []
                        while True:
                            res = model.predict(0, 0)
                            if res is not None:
                                item = [res[0], res[1]]
                                path.append(item)
                            else:
                                break

                        max_index = model._data_arr['Вклад (%)'].idxmax()
                        target_name = get_isa_name(str(int(max_index)), data_dir)
                        viewer_data = {}
                        result_dict = model._data_arr['Вклад (%)'].to_dict()
                        str_holder = []
                        for key in result_dict:
                            name = get_isa_name(str(int(key)), data_dir)
                            str_holder.append(f"Источник: {name} | Вклад: {round(result_dict[key], 2)} %")
                            viewer_data[name] = str(round(result_dict[key], 2))
                        st.session_state['path'] = path
                        st.session_state['expansions'][esp_label]['identification_done'] = True
                        st.session_state['expansions'][esp_label]['identification_result'] = str_holder
                        st.session_state['expansions'][esp_label]['identification_result_one'] = target_name
                        st.session_state['expansions'][esp_label]['predicted_data'] = viewer_data
                        st.session_state["predict"] = True
                        st.rerun()

    with col1:
        grid_start_point = (
        float(config['grid']['left_bottom_corner_lat']), float(config['grid']['left_bottom_corner_lon']))

        cell_size_lat = float(config['grid']['cell_size_lat'])
        cell_size_lon = float(config['grid']['cell_size_lon'])

        map_center = (config['grid']['map_center_lat'], config['grid']['map_center_lon'])

        m = folium.Map(location=map_center, zoom_start=13.5)
        '''
        if st.session_state["predict"]:
            path = st.session_state['path']
            for item in path:
                st.session_state["marker_position"] = (item[0], item[1])

                marker_x, marker_y = st.session_state["marker_position"]
                data = st.session_state['history']
                data.append([marker_y, marker_x])
                st.session_state['history'] = data
                lat1 = grid_start_point[0] - cell_size_lat / 2 + marker_x * cell_size_lat
                lon1 = grid_start_point[1] - cell_size_lon / 2 + marker_y * cell_size_lon
                lat2 = lat1 + cell_size_lat
                lon2 = lon1 + cell_size_lon

                polygon = folium.Polygon(
                    locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                    color='green',
                    fill=True,
                    fill_opacity=0.5,
                    border=0.05,
                )
                m.add_child(polygon)
        '''
        isa_coords = pd.read_csv(
            os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + "system_isa_coords.csv", dtype={'Name': str})
        analyzers_coords = pd.read_csv(os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/" + "system_analyzer_coords.csv")

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
                        if st.session_state["predict"]:
                            last_esp_label = list(st.session_state['expansions'].keys())[-1]
                            isa_data = st.session_state['expansions'][last_esp_label]['predicted_data']
                            #isa_data = st.session_state['expansions']['Превышение 14.01.2023 | 00:00']['predicted_data']
                            folium.Marker(
                                location=[(lat1 + lat2) / 2 - 0.0005, (lon1 + lon2) / 2],
                                icon=folium.DivIcon(
                                    html='<div style="font-size: 16px; color: black;">{}</div>'.format(row["Name"]))
                            ).add_to(m)
                            polygon = folium.Polygon(
                                locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                                color='red',
                                fill=True,
                                fill_opacity=0.5,
                                border=0.05,
                                popup=folium.Popup(
                                    f'<div style="font-size: 30px;">{isa_data[row["Name"]]}%</div>',
                                    max_width=300
                                )
                            )
                            m.add_child(polygon)
                            flag_isa = 1
                            continue
                        else:
                            folium.Marker(
                                location=[(lat1 + lat2) / 2 - 0.0005, (lon1 + lon2) / 2],
                                icon=folium.DivIcon(
                                    html='<div style="font-size: 16px; color: black;">{}</div>'.format(row["Name"]))
                            ).add_to(m)
                            polygon = folium.Polygon(
                                locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                                color='red',
                                fill=True,
                                fill_opacity=0.5,
                                border=0.05,
                            )
                            m.add_child(polygon)
                            flag_isa = 1
                            continue
                flag_analyzer = 0
                for index, row in analyzers_coords.iterrows():
                    if i == row['y'] and j == row['x']:
                        if st.session_state["predict"]:
                            last_esp_label = list(st.session_state['expansions'].keys())[-1]
                            analyzer_data = st.session_state['expansions'][last_esp_label]['analyzers_values']
                            #analyzer_data = st.session_state['expansions']['Превышение 14.01.2023 | 00:00']['analyzers_values']
                            folium.Marker(
                                location=[(lat1 + lat2) / 2 - 0.0004, (lon1 + lon2) / 2],
                                icon=folium.DivIcon(
                                    html='<div style="font-size: 16px; color: black;">{}</div>'.format(row["Name"]))
                            ).add_to(m)
                            polygon = folium.Polygon(
                                locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                                color='blue',
                                fill=True,
                                fill_opacity=0.5,
                                border=0.05,
                                popup=folium.Popup(
                                    f'<div style="font-size: 30px;">{analyzer_data[row["Name"]]}</div>',
                                    max_width=300
                                ),
                            )
                            m.add_child(polygon)
                            flag_analyzer = 1
                            continue
                        else:
                            folium.Marker(
                                location=[(lat1 + lat2) / 2 - 0.0004, (lon1 + lon2) / 2],
                                icon=folium.DivIcon(
                                    html='<div style="font-size: 16px; color: black;">{}</div>'.format(row["Name"]))
                            ).add_to(m)
                            polygon = folium.Polygon(
                                locations=[(lat1, lon1), (lat1, lon2), (lat2, lon2), (lat2, lon1)],
                                color='blue',
                                fill=True,
                                fill_opacity=0.5,
                                border=0.05,
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

        folium_static(m, width=1300, height=1000)