from typing import Union, List
import numpy as np
import pandas as pd
import re
from influxdb import InfluxDBClient

from .dsm_timeseries import dsm_timeseries


def read_csv(filepath: str, time_interval: str, value_column_name: str, time_column_name: str, header: int = 0,
             sep: str = ',', fill: str = False, fill_method: str = 'mean', time_format: str = None) -> dsm_timeseries:
    """
    Method for reading csv file into dsm timeseries structure
    Method using default pd.DataFrame method for read and construct DSM object

    :param fill_method:
    :param filepath: path of csv file (str)
    :param time_interval: time interval in dataframe, using for make dsm struct. Example: 1m, 5m, 2h, 5h etc. (str)
    :param value_column_name: name of float value column (str)
    :param time_column_name: name of datetime value column (str)
    :param header: binary parameter about the presence of a header (header string number or zero for not num) (int)
    :param sep: values separator of csv file (str)
    :param fill: binary parameter about need a fill NaN values in dataframe (bool)
    :param fill_method: method of fill dataframe. Possible: 'mean' or 'zero' (str)
    :param time_format: datetime column format if it is str (str)
    :return: dsm_timeseries structure object contains filled data, interval
    """
    try:
        df = pd.read_csv(filepath, header=header, sep=sep)
    except:
        raise ValueError(f"Cannot convert input file to dataframe")
    if fill:
        df = fillna(df, fill_method)

    obj = dsm_timeseries('Unnamed', df, value_column_name, time_interval, time_column_name, time_format)

    return obj


def read_xlsx(filepath: str, time_interval: str, value_column_name: str, time_column_name: str, header: int = 0,
              fill: str = False, fill_method: str = 'mean', time_format: str = None) -> int:
    """
    Method for reading xlsx file into dsm timeseries structure
    Method using default pd.DataFrame method for read and construct DSM object

    :param fill_method:
    :param filepath: path of xlsx file (str)
    :param time_interval: time interval in dataframe, using for make dsm struct. Example: 1m, 5m, 2h, 5h etc. (str)
    :param value_column_name: name of float value column (str)
    :param time_column_name: name of datetime value column (str)
    :param header: binary parameter about the presence of a header (header string number or zero for not num) (int)
    :param fill: binary parameter about need a fill NaN values in dataframe (bool)
    :param fill_method: method of fill dataframe. Possible: 'mean' or 'zero' (str)
    :param time_format: datetime column format if it is str (str)
    :return: dsm_timeseries structure object contains filled data, interval
    """
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
    except:
        raise ValueError(f"Cannot convert input file to dataframe")
    if fill:
        df = fillna(df, fill_method)

    obj = dsm_timeseries('Unnamed', df, value_column_name, time_interval, time_column_name, time_format)

    return obj


def __using_transform(value: float, bias: float, limit: float) -> float:
    """
    Function for convert single value from absolute to PDK

    :param value: target value (float)
    :param limit: limit of pdk values per 1 data point (float)
    :param bias: data transformation offset for every data point (float)
    :return: transformed value (float)
    """
    return bias + (value / limit)


def __using_reverse_transform(value: float, bias: float, limit: float) -> float:
    """
    Function for convert single value from PDK to absolute

    :param value: target value (float)
    :param limit: limit of pdk values per 1 data point (float)
    :param bias: data transformation offset for every data point (float)
    :return: transformed value (float)
    """
    return (value * limit) - bias


def transform(data: Union[pd.DataFrame, np.ndarray, dsm_timeseries], limit_pdk_value: float, bias: float,
              value_column_index: int = None, value_column_name: str = None) -> Union[pd.DataFrame, np.ndarray, dsm_timeseries]:
    """
    Method for convert target float values to PDK points

    :param data: dataframes contains target float values (pd.DataFrame, np.ndarray, dsm_timeseries)
    :param limit_pdk_value: limit of pdk values per 1 data point (float)
    :param bias: data transformation offset for every data point (float)
    :param value_column_index: required only for np.ndarray data, integer index of target column (int)
    :param value_column_name: required only for pd.DataFrame data, str name of target column (str)
    :return: data array with transformed target values (using kx + b) (pd.DataFrame, np.ndarray, dsm_timeseries)
    """
    if isinstance(data, pd.DataFrame):
        if value_column_name is None or value_column_name not in data.columns:
            raise ValueError(f"Missing param value_column_name or {value_column_name} not in dataframe.")
        data[value_column_name] = data[value_column_name].apply(__using_transform, args=(bias, limit_pdk_value))
        return data
    if isinstance(data, np.ndarray):
        if data.ndim >= value_column_index or value_column_index is None:
            raise ValueError(f"Missing param value_column_index or value_column_index > number of array columns")
        data[:, value_column_index] = np.apply_along_axis(__using_transform, 0, data[:, value_column_index],
                                                          bias=bias, limit=limit_pdk_value)
    if isinstance(data, dsm_timeseries):
        df = data.data
        value_column_name = data.value_column_name
        df[value_column_name] = df[value_column_name].apply(__using_transform, args=(bias, limit_pdk_value))
        data._data = df
        return data


def reverse_transform(data: Union[pd.DataFrame, np.ndarray, dsm_timeseries], limit_pdk_value: float, bias: float,
                      value_column_index: int = None, value_column_name: str = None) -> Union[pd.DataFrame, np.ndarray, dsm_timeseries]:
    """
    Method for convert target float values to absolute values from PDF points

    :param data: dataframes contains target PDK values (pd.DataFrame, np.ndarray, dsm_timeseries)
    :param limit_pdk_value: limit of pdk values per 1 data point (float)
    :param bias: data transformation offset for every data point (float)
    :param value_column_index: required only for np.ndarray data, integer index of target column (int)
    :param value_column_name: required only for pd.DataFrame data, str name of target column (str)
    :return: data array with transformed target values (using kx + b) (pd.DataFrame, np.ndarray, dsm_timeseries)
    """
    if isinstance(data, pd.DataFrame):
        if value_column_name is None or value_column_name not in data.columns:
            raise ValueError(f"Missing param value_column_name or {value_column_name} not in dataframe.")
        data[value_column_name] = data[value_column_name].apply(__using_reverse_transform, args=(bias, limit_pdk_value))
        return data
    if isinstance(data, np.ndarray):
        if data.ndim >= value_column_index or value_column_index is None:
            raise ValueError(f"Missing param value_column_index or value_column_index > number of array columns")
        data[:, value_column_index] = np.apply_along_axis(__using_reverse_transform, 0, data[:, value_column_index],
                                                          bias=bias, limit=limit_pdk_value)
    if isinstance(data, dsm_timeseries):
        df = data.data
        value_column_name = data.value_column_name
        df[value_column_name] = df[value_column_name].apply(__using_reverse_transform, args=(bias, limit_pdk_value))
        data._data = df
        return data


def fillna(data: Union[pd.DataFrame, np.ndarray, dsm_timeseries], method: str) -> Union[pd.DataFrame, np.ndarray, dsm_timeseries]:
    """
    Method for fill NA float values in dataframe
    Warning: working only with float values

    :param data: dataframes contains float target and features values (pd.DataFrame, np.ndarray, dsm_timeseries)
    :param method: filling method, possible is "mean", "min", "max", "short_mean", "zero" (str)
    :return: data array with filled float values (pd.DataFrame, np.ndarray, dsm_timeseries)
    """
    if isinstance(data, pd.DataFrame):
        match method:
            case 'mean':
                return data.fillna(data.mean())
            case 'min':
                return data.fillna(data.min())
            case 'max':
                return data.fillna(data.max())
            case 'zero':
                return data.fillna(0)
            case 'short_mean':
                try:
                    if data.shift(1) != np.NaN and data.shift(-1) != np.NaN:
                        return data.fillna((data.shift(1) + data.shift(-1)) / 2)
                    else:
                        return data.fillna(data.mean())
                except:
                    return data.fillna(data.mean())
            case _:
                raise ValueError("Incorrect fill method: {}".format(method))
    if isinstance(data, np.ndarray):
        match method:
            case 'mean':
                return np.nan_to_num(data, nan=np.nanmean(data))
            case 'min':
                return np.nan_to_num(data, nan=np.nanmin(data))
            case 'max':
                return np.nan_to_num(data, nan=np.nanmax(data))
            case 'zero':
                return np.nan_to_num(data, nan=0)
            case 'short_mean':
                try:
                    nan_indices = np.isnan(data)
                    filled_data = data.copy()
                    valid_indices = ~nan_indices
                    shift_up = np.roll(filled_data, 1)
                    shift_down = np.roll(filled_data, -1)
                    shift_up[0] = np.nan
                    shift_down[-1] = np.nan
                    filled_data[nan_indices] = (shift_up + shift_down) / 2
                    filled_data[valid_indices] = data[valid_indices]
                    return filled_data
                except:
                    return np.nan_to_num(data, nan=np.nanmean(data))
            case _:
                raise ValueError("Incorrect fill method: {}".format(method))
    if isinstance(data, dsm_timeseries):
        df = data.data
        match method:
            case 'mean':
                df = df.fillna(df.mean())
                data._data = df
                return data
            case 'min':
                df = df.fillna(df.min())
                data._data = df
                return data
            case 'max':
                df = df.fillna(df.max())
                data._data = df
                return data
            case 'zero':
                df = df.fillna(0)
                data._data = df
                return data
            case 'short_mean':
                try:
                    if df.shift(1) != np.NaN and df.shift(-1) != np.NaN:
                        df = df.fillna((df.shift(1) + df.shift(-1)) / 2)
                        data._data = df
                        return data
                    else:
                        df = df.fillna(df.mean())
                        data._data = df
                        return data
                except:
                    df = df.fillna(df.mean())
                    data._data = df
                    return data
            case _:
                raise ValueError("Incorrect fill method: {}".format(method))


def __convert_to_minutes(time_str: str) -> int:
    """
    Method for convert str time interval to minutes count
    Warning: time interval must be >1m and <24h

    :param time_str: string value of interval (pd.DataFrame, np.ndarray, dsm_timeseries)
    :return: count of minutes in interval (int)
    """
    total_minutes = 0
    matches = re.findall(r'(\d+)([dhm]?)', time_str)

    for value, unit in matches:
        value = int(value)
        if unit == 'm':
            total_minutes += value
        elif unit == 'h':
            total_minutes += value * 60
        else:
            raise ValueError("Incorrect interval format")
    return total_minutes


def time_rebase(data: Union[pd.DataFrame, dsm_timeseries], new_interval: str, time_column_name: str) -> Union[pd.DataFrame, dsm_timeseries]:
    """
    Method for rebase datetime values in dataframe
    Warning: working only with datetime values, the first two values must have a strict interval

    :param data: dataframes contains datetime values (pd.DataFrame, dsm_timeseries)
    :param new_interval: new interval value between two dates in dataframe. Example: 5m, 10m, 1h etc. (str)
    :param time_column_name: requires only for pd.DataFrame input, for identify datetime main column (str)
    :return: data array with rebased datetime values (pd.DataFrame, dsm_timeseries)
    """
    new_minutes_interval = __convert_to_minutes(new_interval)
    if isinstance(data, pd.DataFrame):
        if data.shape[0] >= 2:
            first_value = data.iloc[0][time_column_name]
            second_value = data.iloc[1][time_column_name]

            time_diff = second_value - first_value
            minutes = time_diff.seconds // 60
            if minutes > new_minutes_interval:
                raise ValueError("New interval is less than current")
            else:
                data_resampled = data.groupby(
                    pd.Grouper(key=time_column_name, freq=f'{new_minutes_interval}T')).mean().reset_index()
                return data_resampled
        else:
            raise ValueError("Input dataframe contains 1 value")
    if isinstance(data, dsm_timeseries):
        df = data.data
        if df.df[0] >= 2:
            first_value = df.iloc[0][time_column_name]
            second_value = df.iloc[1][time_column_name]

            time_diff = second_value - first_value
            minutes = time_diff.seconds // 60
            if minutes > new_minutes_interval:
                raise ValueError("New interval is less than current")
            else:
                df_resampled = df.groupby(
                    pd.Grouper(key=data.time_column_name, freq=f'{new_minutes_interval}T')).mean().reset_index()
                data._data = df_resampled
                data._interval = data._format_time(0, new_minutes_interval)
                return df_resampled
        else:
            raise ValueError("Input dataframe contains 1 value")


def load_influx(dataframe: Union[pd.DataFrame, dsm_timeseries],
                measurement_name: str,
                host: str,
                port: int,
                username: str,
                password: str,
                database: str,
                time_column_name: str = None) -> None:
    if isinstance(dataframe, dsm_timeseries):
        df = dataframe
        dataframe = dataframe.data
        time_column_name = df._time_column_name
    influxdb_json = __create_influxdb_json(dataframe, measurement_name, time_column_name)
    try:
        client = InfluxDBClient(host, port, username, password, database)
        client.switch_database(database)
        #client.drop_measurement(measurement_name)
        client.write_points(influxdb_json)
    except:
        raise ValueError("Can't load dataframe into influxdb")


def __create_influxdb_json(dataframe, measurement_name, time_column_name):
    influxdb_json = []
    for _, row in dataframe.iterrows():
        measurement = {
            'measurement': measurement_name,
            'tags': {},
            'time': row[time_column_name],
            'fields': {}
        }
        for column in dataframe.columns:
            if column != time_column_name:
                measurement['fields'][column] = row[column]
        influxdb_json.append(measurement)
    return influxdb_json


def __drop_mes(client, measurement_name):
    client.drop_measurement(measurement_name)