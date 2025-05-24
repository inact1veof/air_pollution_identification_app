import datetime
import time
from datetime import datetime as dt
import streamlit as st
from influxdb import InfluxDBClient
import os
from dotenv import load_dotenv

from .models.dsm_timeseries import dsm_timeseries
from .models.TDaysAVR import TDaysAVR
from .models.SDaysAVR import SDaysAVR
from .models.EMLR import EMLR
from .models.EMNN import EMNN
from .models.HW import HW
from .models.DayFeaturesLR import DayFeaturesLR
from .models.DayFeaturesNN import DayFeaturesNN
from .models.STA import STA
from .models.SARIMA import SARIMA
from .models.NaiveSelector import NaiveSelector
from .models.SDaysSelector import SDaysSelector
from .models.NNSelector import NNSelector
from .models.metrics import rmse
from .models.Utils import load_influx, transform, read_csv, read_xlsx
import os
import pandas as pd

def get_data(initial_day, host, port, username, password, database, models, measurement):
    client = InfluxDBClient(host, port, username, password, database)
    client.switch_database(database)
    iday = dt.strptime(initial_day, '20%y-%m-%d')
    current_day = iday.strftime("20%y-%m-%d")
    print("Processing day: " + current_day)
    iday += datetime.timedelta(days=1)
    next_day = iday.strftime("20%y-%m-%d")
    str_models = ",".join([f'"{item}"' for item in models])
    q = f'select {str_models} FROM ' + measurement + " WHERE time >= '" + current_day + "T00:00:00.000Z' and time <= '" + next_day + "T00:00:00.000Z' LIMIT 100000"
    ResultSet = client.query(q)
    df_prod = pd.DataFrame(ResultSet.get_points())

    df_prod['time'] = pd.to_datetime(df_prod['time'])
    df_prod = df_prod.set_index('time')
    return df_prod


def get_page():
    st.title('Использование прогнозных моделей')

    st.write('Данная страница предназначена для построение демо-прогноза')
    st.write('Все модели запускаются с параметром method="Last" для получения проноза на сутки вперед')

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) + "/data"
    file_names = os.listdir(data_dir)

    selected_file_forecast = st.selectbox("Выберите файл для совершения прогноза", file_names)

    value_column_name = st.text_input(f'Введите наименование столбца-таргета:', 'Value')

    time_column_name = st.text_input(f'Введите наименование столбца дата/время:', 'Time')
    day_points_field = st.text_input(f'Введите количество временных точек в сутка:', '72')

    options_base = st.multiselect(
        "Выберите базовые модели прогнозирования",
        ("TDaysAVR", "SDaysAVR", "HW", "SARIMA", "STA", "DayFeaturesLR", "DayFeaturesNN")
    )
    options_advanced = st.multiselect(
        "Выберите ансамблевые/селективные модели прогнозирования",
        ("EMLR", "EMNN", "NaiveSelector", "SDaysSelector", "NNSelector")
    )

    if st.button('Выполнить прогноз'):
        if len(options_base) == 0:
            st.error("Вы не выбрали ни одной базовой модели")
            st.stop()
        load_dotenv(dotenv_path="../../.env")

        day_points = int(day_points_field)

        model_dictionary = {'TDaysAVR': 'Forecast_copy_last_day',
                            'SDaysAVR': 'Forecast_N_days_average',
                            'HW': 'Forecast_Holt-Winters',
                            'EMNN': 'Forecast_CM&MLP',
                            'STA': 'Forecast_PAR',
                            'DayFeaturesLR': 'Forecast_SPR',
                            'DayFeaturesNN': 'Forecast_SPR&MLP',
                            'EMLR': 'Forecast_CM&LR',
                            'SARIMA': 'Forecast_SARIMA',
                            'NaiveSelector': 'Forecast_Naive_Choosing',
                            'SDaysSelector': 'Forecast_N_days_Choosing',
                            'NNSelector': 'Forecast_MLP_Choosing'
        }

        rmse_dictionary = {'TDaysAVR': 'Forecast_copy_last_day_RMSE',
                            'SDaysAVR': 'Forecast_N_days_average_RMSE',
                            'HW': 'Forecast_Holt-Winters_RMSE',
                            'EMNN': 'Forecast_CM&MLP_RMSE',
                            'STA': 'Forecast_PAR_RMSE',
                            'DayFeaturesLR': 'Forecast_SPR_RMSE',
                            'DayFeaturesNN': 'Forecast_SPR&MLP_RMSE',
                            'EMLR': 'Forecast_CM&LR_RMSE',
                            'SARIMA': 'Forecast_SARIMA_RMSE',
                            'NaiveSelector': 'Forecast_Naive_Choosing_RMSE',
                            'SDaysSelector': 'Forecast_N_days_Choosing_RMSE',
                            'NNSelector': 'Forecast_MLP_Choosing_RMSE'
        }

        model_list_base = [model_dictionary[key] for key in options_base if key in model_dictionary]
        model_list_advanced = [model_dictionary[key] for key in options_advanced if key in model_dictionary]

        model_list = []
        model_list.extend(model_list_base)
        model_list.extend(model_list_advanced)

        models_base = []
        models_advanced = []

        model_base_names = []
        model_advanced_names = []

        for name in options_base:
            if name in globals():
                models_base.append(globals()[name]())
                model_base_names.append(name)

        for name in options_advanced:
            if name in globals():
                models_advanced.append(globals()[name](base_models=models_base, pretrained=True))
                model_advanced_names.append(name)

        model_base_names.extend(model_advanced_names)


        progress_bar = st.progress(0)
        try:
            if selected_file_forecast[-1] == 'v':
                df = read_csv(data_dir + '/' + selected_file_forecast, '20m', value_column_name, time_column_name)
            else:
                df = read_xlsx(data_dir + '/' + selected_file_forecast, '20m', value_column_name, time_column_name)
        except:
            st.error("Входной датафрейм имеет некорректный формат")
            st.stop()

        df_zeros = df._data.copy(deep=True)
        df_zeros = df_zeros[-day_points:]
        for item in model_list:
            df_zeros[item] = float(0)

        if "SARIMA" in options_base:
            df_zeros['Forecast_SARIMA'] = df_zeros['Forecast_SARIMA'].astype(int)


        df_zeros['Value'] = df._data['Value'][-day_points:].values
        try:
            load_influx(
                dataframe=df_zeros,
                measurement_name=os.getenv("INFLUXDB_MEASUREMENT"),
                host=os.getenv("INFLUXDB_HOST"),
                port=os.getenv("INFLUXDB_PORT"),
                username=os.getenv("INFLUXDB_USER"),
                password=os.getenv("INFLUXDB_PASSWORD"),
                database=os.getenv("INFLUXDB_DATABASE"),
                time_column_name=time_column_name
            )
        except:
            st.error("Загрузка в базу данных не удалась")
            st.stop()
        counter = 0
        for model in models_base:
            progress_bar.progress((counter+1) / len(model_base_names))
            if isinstance(model, STA):
                model.fit(df, day_points)
                model_result = model.predict(method='Last')
            elif isinstance(model, DayFeaturesLR):
                model.fit(df, day_points)
                model_result = model.predict(df, method='Last')
            elif isinstance(model, DayFeaturesNN):
                model.fit(df, day_points)
                model_result = model.predict(df, method='All')
                model_result = model_result[-day_points:]
            elif isinstance(model, SARIMA):
                model.fit(df, 14,day_points)
                model_result = model.predict(method='Last')
            else:
                model_result = model.predict(df, method='Last')
            df_zeros[model_dictionary[model_base_names[counter]]] = model_result
            df_zeros[rmse_dictionary[model_base_names[counter]]] = rmse(df_zeros, value_column_name, model_list[counter], time_column_name)
            counter += 1

        for model in models_advanced:
            progress_bar.progress((counter + 1) / len(model_base_names))
            if isinstance(model, NaiveSelector):
                model.fit(df,5, day_points)
                model_result = model.predict(df, method='All')
                model_result = model_result[-day_points:]
                df_zeros[model_dictionary[model_base_names[counter]]] = model_result
                df_zeros[rmse_dictionary[model_base_names[counter]]] = rmse(df_zeros, value_column_name,model_list[counter], time_column_name)
            elif isinstance(model, SDaysSelector):
                model.fit(df,14, day_points)
                model_result = model.predict(df, method='All')
                model_result = model_result[-day_points:]
                df_zeros[model_dictionary[model_base_names[counter]]] = model_result
                df_zeros[rmse_dictionary[model_base_names[counter]]] = rmse(df_zeros, value_column_name,model_list[counter], time_column_name)
            elif isinstance(model, NNSelector):
                model.fit(df,28, day_points)
                model_result = model.predict(df, method='All')
                model_result = model_result[-day_points:]
                df_zeros[model_dictionary[model_base_names[counter]]] = model_result
                df_zeros[rmse_dictionary[model_base_names[counter]]] = rmse(df_zeros, value_column_name,model_list[counter], time_column_name)
            else:
                model.fit(df, day_points)
                model_result = model.predict(df, method='Last')
                df_zeros[model_dictionary[model_base_names[counter]]] = model_result
                df_zeros[rmse_dictionary[model_base_names[counter]]] = rmse(df_zeros, value_column_name,model_list[counter], time_column_name)
            counter += 1

        try:
            load_influx(
                dataframe=df_zeros,
                measurement_name=os.getenv("INFLUXDB_MEASUREMENT"),
                host=os.getenv("INFLUXDB_HOST"),
                port=os.getenv("INFLUXDB_PORT"),
                username=os.getenv("INFLUXDB_USER"),
                password=os.getenv("INFLUXDB_PASSWORD"),
                database=os.getenv("INFLUXDB_DATABASE"),
                time_column_name=time_column_name
            )
        except:
            st.error("Загрузка в базу данных не удалась")
            st.stop()
        st.success('Прогноз успешно выполнен, результаты доступны в средстве визуализации Grafana')