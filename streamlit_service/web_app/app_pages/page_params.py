import streamlit as st
import configparser
import os

def save_to_config(config_file, section, key, value):
    config = configparser.ConfigParser()
    config.read(config_file)
    config.set(section, key, value)

    with open(config_file, 'w') as configfile:
        config.write(configfile)

def get_page():
    st.title("Параметры идентификации источника выбросов")
    st.markdown(
        """
        <style>
        .s-button {
            width: 370px;
            background-color: lightgrey;
            color: dark;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            border: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    block_expander_grid = st.expander(label="Параметры сетки карты", expanded=False)
    block_expander_qlearn = st.expander(label="Параметры Q-обучения", expanded=False)
    block_expander_data = st.expander(label="Параметры использования данных", expanded=False)

    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    config = configparser.ConfigParser()
    config.read(f'{config_dir}/config.ini')

    with block_expander_data:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data"
        file_names = os.listdir(data_dir)

        isa_square_config_index = file_names.index(config['data']['isa_square_pos_filename']) if config['data']['isa_square_pos_filename'] in file_names else None
        isa_point_config_index = file_names.index(config['data']['isa_point_pos_filename']) if config['data']['isa_point_pos_filename'] in file_names else None
        analyzers_pos_filename = file_names.index(config['data']['analyzers_pos_filename']) if config['data']['analyzers_pos_filename'] in file_names else None
        learn_dataframe_filename = file_names.index(config['data']['learn_dataframe_filename']) if config['data']['learn_dataframe_filename'] in file_names else None
        predict_dataframe_filename = file_names.index(config['data']['predict_dataframe_filename']) if config['data']['predict_dataframe_filename'] in file_names else None
        nn_predictor_filename = file_names.index(config['data']['nn_predictor_filename']) if config['data']['nn_predictor_filename'] in file_names else None

        selected_file_isa_point = st.selectbox("Выберите файл с позициями точечных ИЗА", file_names,
                                               index=isa_point_config_index)
        selected_file_isa_square = st.selectbox("Выберите файл с позициями площадных ИЗА", file_names,
                                               index=isa_square_config_index)
        selected_file_analyzers = st.selectbox("Выберите файл позициями постов контоля", file_names,
                                               index=analyzers_pos_filename)
        selected_file_learn = st.selectbox("Выберите файл с обучающим датасетом для Q-learning", file_names,
                                               index=learn_dataframe_filename)
        selected_file_nn_predictor = st.selectbox("Выберите файл моделью нейронной сети", file_names,
                                               index=nn_predictor_filename)
        selected_file_predict = st.selectbox("Выберите файл для построения идентификации", file_names,
                                               index=predict_dataframe_filename)
        arr = [selected_file_isa_point, selected_file_isa_square, selected_file_analyzers, selected_file_learn, selected_file_nn_predictor, selected_file_predict]

        for i in range(len(arr)):
            if arr[i] is None:
                arr[i] = ''

        if st.button("Сохранить параметры файлов"):
            try:
                config_file = config_dir + "/config.ini"
                save_to_config(config_file, 'data', 'isa_point_pos_filename', arr[0])
                save_to_config(config_file, 'data', 'isa_square_pos_filename', arr[1])
                save_to_config(config_file, 'data', 'analyzers_pos_filename', arr[2])
                save_to_config(config_file, 'data', 'learn_dataframe_filename', arr[3])
                save_to_config(config_file, 'data', 'predict_dataframe_filename', arr[5])
                save_to_config(config_file, 'data', 'nn_predictor_filename', arr[4])
                st.success("Вы успешно обновили параметры файлов")
            except:
                st.write("Не удалось сохранить новые параметры")


    with block_expander_grid:
        h_size = st.text_input(f'Количество ячеек по высоте', config['grid']['h_size'])
        l_size = st.text_input(f'Количество ячеек по ширине', config['grid']['l_size'])
        map_center_lat = st.text_input(f'Широта центра карты', config['grid']['map_center_lat'])
        map_center_lon = st.text_input(f'Долгота центра карты', config['grid']['map_center_lon'])
        left_bottom_corner_lat = st.text_input(f'Широта левого нижнего угла карты', config['grid']['left_bottom_corner_lat'])
        left_bottom_corner_lon = st.text_input(f'Долгота левого нижнего угла карты', config['grid']['left_bottom_corner_lon'])
        cell_size_lat = st.text_input(f'Высота ячейки в градусах', config['grid']['cell_size_lat'])
        cell_size_lon = st.text_input(f'Ширина ячейки в градусах', config['grid']['cell_size_lon'])

        if st.button("Сохранить параметры сетки на карте"):
            try:
                config_file = config_dir + "/config.ini"
                save_to_config(config_file, 'grid', 'h_size', h_size)
                save_to_config(config_file, 'grid', 'l_size', l_size)
                save_to_config(config_file, 'grid', 'map_center_lat', map_center_lat)
                save_to_config(config_file, 'grid', 'map_center_lon', map_center_lon)
                save_to_config(config_file, 'grid', 'left_bottom_corner_lat', left_bottom_corner_lat)
                save_to_config(config_file, 'grid', 'left_bottom_corner_lon', left_bottom_corner_lon)
                save_to_config(config_file, 'grid', 'cell_size_lat', cell_size_lat)
                save_to_config(config_file, 'grid', 'cell_size_lon', cell_size_lon)
                st.success("Вы успешно обновили параметры")
            except:
                st.write("Не удалось сохранить новые параметры")

    with block_expander_qlearn:
        learning_rate = st.text_input(f'Learning rate', config['learn']['learning_rate'])
        discount_factor = st.text_input(f'Discount factor', config['learn']['discount_factor'])
        epsilon = st.text_input(f'Epsilon', config['learn']['epsilon'])

        if st.button("Сохранить параметры обучения"):
            try:
                config_file = config_dir + "/config.ini"
                save_to_config(config_file, 'learn', 'learning_rate', learning_rate)
                save_to_config(config_file, 'learn', 'discount_factor', discount_factor)
                save_to_config(config_file, 'learn', 'epsilon', epsilon)
                st.success("Вы успешно обновили параметры")
            except:
                st.write("Не удалось сохранить новые параметры")

