import streamlit as st
import os
import sys
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(parent_dir)
from DIM.Simulators import emissions, learn, weather
from .models.Utils import read_csv, read_xlsx, transform, load_influx
from .models.dsm_timeseries import dsm_timeseries

def get_page():
    st.title("Генерация и получение данных")
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

    block_expander_forecast_value = st.expander(label="Ввод измерений концентраций ВВ для прогноза",expanded=False)
    block_expander_forecast_meteo = st.expander(label="Ввод метеоданных", expanded=False)
    block_expander_isa_simulator = st.expander(label="Симулятор работы ИЗА", expanded=False)
    block_expander_weather_simulator = st.expander(label="Симлятор погодных условий", expanded=False)
    block_expander_rd = st.expander(label="Генерация обучающего датасета", expanded=False)
    block_expender_isa = st.expander(label="Загрузить положения точечного ИЗА", expanded=False)
    block_expender_isa_sq = st.expander(label="Загрузить положения площадного ИЗА", expanded=False)
    block_expender_analyzers = st.expander(label="Загрузить положения постов контроля", expanded=False)
    block_expender_learn_df = st.expander(label="Загрузить обучающий датасет для Q-learning", expanded=False)
    block_expender_nn_model = st.expander(label="Загрузить предиктивную модель (нейросеть)", expanded=False)
    block_expender_identification = st.expander(label="Загрузить временной ряд для идентификации", expanded=False)
    block_expender_loaded = st.expander(label="Загруженные файлы", expanded=False)

    with block_expander_forecast_value:
        uploaded_file = st.file_uploader("Выберите файл со значениями концентраций ВВ (csv, xlsx)", type=["csv", "xlsx"])
        value_column_name = st.text_input(f'Введите наименование столбца-таргета:', 'Value')
        time_column_name = st.text_input(f'Введите наименование столбца дата/время:', 'Time')
        if st.button("Загрузить данные концентраций"):
            #try:
            save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
            file_name = 'forecast_value_' + uploaded_file.name
            save_dir = save_dir + file_name
            with open(save_dir, "wb") as f:
                f.write(uploaded_file.getbuffer())
            if uploaded_file.name[-1] == 'v':
                df = read_csv(save_dir, '20m', value_column_name, time_column_name)
            else:
                df = read_xlsx(save_dir,'20m', value_column_name, time_column_name)

            data = df._data.copy(deep=True)

            df2 = dsm_timeseries('sample', data, value_column_name, '20m', time_column_name)

            res = transform(df2, 1000, 0)._data
            res.rename(columns={value_column_name: 'PDK_value'}, inplace=True)

            load_df = pd.merge(df._data, df2._data, on=time_column_name)

            load_influx(load_df,
                        'use_case_5_CH4',
                        '185.244.51.57',
                        8186,
                        'admin',
                        'pas2023',
                        'Ch',
                        'Time')

            st.write(f"Файл успешно загружен как: {file_name}, а также загружен в БД")
            #except:
                #st.write("Ошибка сохранения")

    with block_expander_forecast_meteo:
        uploaded_file = st.file_uploader("Выберите файл со значениями погоды (csv, xlsx)", type=["csv", "xlsx"])
        time_column_name_met = st.text_input(f'Введите наименование столбца дата/время для файла погоды:', 'Time')
        if st.button("Загрузить данные погоды"):
            try:
                save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
                file_name = 'forecast_weather_' + uploaded_file.name
                save_dir = save_dir + file_name
                with open(save_dir, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                if uploaded_file.name[-1] == 'v':
                    df = pd.read_csv(save_dir)
                else:
                    df = pd.read_excel(save_dir, engine='openpyxl')

                load_influx(df,
                            'use_case_5_CH4',
                            '185.244.51.57',
                            8186,
                            'admin',
                            'pas2023',
                            'Ch',
                            'Time')

                st.write(f"Файл успешно загружен как: {file_name}, а также загружен в БД")
            except:
                st.write("Ошибка сохранения")

    with block_expender_isa_sq:
        uploaded_file = st.file_uploader("Выберите файл с положениями площадных ИЗА (txt)", type=["txt"])
        if st.button("Сохранить данные площадных ИЗА"):
            try:
                save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
                file_name = 'isa_loaded_square_' + uploaded_file.name
                save_dir = save_dir + file_name
                with open(save_dir, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Файл успешно загружен как: {file_name}")
            except:
                st.write("Ошибка сохранения")

    with block_expender_identification:
        uploaded_file = st.file_uploader("Выберите файл для идентификации (csv)", type=["csv"])
        if st.button("Сохранить данные идентификации"):
            try:
                save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
                file_name = 'identification_' + uploaded_file.name
                save_dir = save_dir + file_name
                with open(save_dir, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Файл успешно загружен как: {file_name}")
            except:
                st.write("Ошибка сохранения")

    with block_expender_nn_model:
        uploaded_file = st.file_uploader("Выберите файл модели предобученной нейронной сети")
        if st.button("Сохранить модель"):
            try:
                save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
                file_name = 'nn_model_' + uploaded_file.name
                save_dir = save_dir + file_name
                with open(save_dir, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Файл успешно загружен как: {file_name}")
            except:
                st.write("Ошибка сохранения")

    with block_expender_learn_df:
        uploaded_file = st.file_uploader("Выберите файл обучающим датасетом для модели Q-learning", type=["csv"])
        if st.button("Сохранить обучающий датасет"):
            try:
                save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
                file_name = 'q_learn_train_' + uploaded_file.name
                save_dir = save_dir + file_name
                with open(save_dir, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Файл успешно загружен как: {file_name}")
            except:
                st.write("Ошибка сохранения")

    with block_expender_loaded:
        data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data"
        files = os.listdir(data_path)
        if len(files) != 0:
            st.write("Загруженные файлы:")
            for file in files:
                st.write(file)
        else:
            st.write("Загруженных файлов нет")

    with block_expender_isa:
        uploaded_file = st.file_uploader("Выберите файл с положением точечного ИЗА (txt)", type=["txt"])
        if st.button("Сохранить данные ИЗА"):
            try:
                save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
                file_name = 'isa_loaded_point_' + uploaded_file.name
                save_dir = save_dir + file_name
                with open(save_dir, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Файл успешно загружен как: {file_name}")
            except:
                st.write("Ошибка сохранения")

    with block_expender_analyzers:
        uploaded_file = st.file_uploader("Выберите файл с положением постов контроля (txt)", type=["txt"])
        if st.button("Сохранить данные постов контроля"):
            try:
                save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data/"
                file_name = 'analyzers_loaded_' + uploaded_file.name
                save_dir = save_dir + file_name
                with open(save_dir, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.write(f"Файл успешно загружен как: {file_name}")
            except:
                st.write("Ошибка сохранения")

    with block_expander_isa_simulator:
        filename = st.text_input(f'Наименование датасета ИЗА', "")
        start_date = st.date_input(f'Дата старта моделирования ИЗА')
        end_date = st.date_input(f'Дата конца моделирования ИЗА')
        isa_count = st.text_input(f'Количество ИЗА', "")
        interval = st.text_input(f'Интервал моделирования ИЗА (минуты)', "")
        if st.button("Генерировать значения ИЗА"):
            isa_count = int(isa_count)
            interval = int(interval)
            try:
                current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data"
                emissions.make_csv_emmissions(isa_count, start_date, end_date, interval, filename, current_dir)
                st.write("Генерация успешна")
            except:
                st.write("Ошибка генерации")

    with block_expander_weather_simulator:
        filename = st.text_input(f'Наименование датасета погоды', "")
        start_date = st.date_input(f'Дата старта моделирования погоды')
        end_date = st.date_input(f'Дата конца моделирования погоды')
        interval = st.text_input(f'Интервал моделирования погоды (минуты)', "")
        if st.button("Генерировать погоду"):
            interval = int(interval)
            try:
                current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data"
                weather.make_csv_weather(start_date, end_date, interval, filename, current_dir)
                st.write("Генерация успешна")
            except:
                st.write("Ошибка генерации")

    with block_expander_rd:
        filename = st.text_input(f'Наименование обучающего датасета', "")
        lines_count = st.text_input('Число строк в обучающем датасете')
        isa_count = st.text_input('Количество источников')
        if st.button("Сгенерировать датасет"):
            lines_count = int(lines_count)
            isa_count = int(isa_count)
            try:
                current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data"
                learn.generate_learn_df(lines_count, isa_count, filename, current_dir)
                st.write("Генерация успешна")
            except:
                st.write("Ошибка генерации")