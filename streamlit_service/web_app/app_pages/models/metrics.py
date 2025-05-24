import numpy as np
import pandas as pd
import datetime
import padasip as pa
from sklearn.metrics import r2_score


def _get_day_list(df: pd.DataFrame, datetime_column_name: str):
    """
    Method for calculating day list of df

    :param df: user pandas dataframe (pd.DataFrame)
    :param datetime_column_name: column name in df with datetime value (str)
    :returns pd Dataframe (pd.DataFrame) and list of days (list)
    """
    df = df.copy(deep=True)
    df['date'] = df[datetime_column_name].dt.date
    df['time'] = df[datetime_column_name].dt.time
    df = df.set_index(datetime_column_name)

    df_tmp = df.copy(deep=True)
    df_tmp = df_tmp.drop(columns=['time'])

    avg_day = df_tmp.groupby(['date']).sum()
    day_list = list(avg_day.index)
    return df, day_list


def _calculate_mape(x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
    """
    Method for calculating MAPE for 1 day

    :param x1: real values array (np.ndarray)
    :param x2: forecasting values array (np.ndarray)
    :return: array of metric 100-mape (np.ndarray)
    """
    zero_indices = np.where(x1 == 0)[0]

    x1_without_zeros = np.delete(np.array(x1), zero_indices)
    x2_without_zeros = np.delete(np.array(x2), zero_indices)

    mape = np.mean(np.abs((x1_without_zeros - x2_without_zeros) / x1_without_zeros)) * 100
    return 100 - mape


def rmse(df: pd.DataFrame, value_column_name: str, forecast_column_name: str, datetime_column_name: str) -> np.ndarray:
    """
    Method for calculating RMSE for N-day dataframe

    :param df: user pandas dataframe (pd.DataFrame)
    :param value_column_name: name of real values column (str)
    :param forecast_column_name: name of forecast values column (str)
    :param datetime_column_name: name of datetime column (str)
    :return: numpy array with error values
    """
    df = df.copy(deep=True)
    df['RMSE'] = float(0)
    df, day_list = _get_day_list(df, datetime_column_name)
    for i in range(len(day_list)):
        copy1 = df[df['date'].isin([list(day_list)[i]])].copy()[['date', 'time', value_column_name]]
        copy2 = df[df['date'].isin([list(day_list)[i]])].copy()[['date', 'time', forecast_column_name]]
        x1 = np.zeros((len(copy1)))
        x2 = np.zeros((len(copy2)))

        for j in range(len(copy1)):
            x1[j] = copy1.loc[copy1.index[j], value_column_name]
            x2[j] = copy2.loc[copy2.index[j], forecast_column_name]

        rmse_values = pa.misc.RMSE(x1, x2)
        for j in range(len(copy1)):
            df.loc[copy1.index[j], 'RMSE'] = rmse_values
    return np.array(df['RMSE'])


def mape(df: pd.DataFrame, value_column_name: str, forecast_column_name: str, datetime_column_name: str) -> np.ndarray:
    """
    Method for calculating MAPE for N-day dataframe

    :param df: user pandas dataframe (pd.DataFrame)
    :param value_column_name: name of real values column (str)
    :param forecast_column_name: name of forecast values column (str)
    :param datetime_column_name: name of datetime column (str)
    :return: numpy array with error values
    """
    df = df.copy(deep=True)
    df['MAPE'] = float(0)
    df, day_list = _get_day_list(df, datetime_column_name)
    for i in range(len(day_list)):
        copy1 = df[df['date'].isin([list(day_list)[i]])].copy()[['date', 'time', value_column_name]]
        copy2 = df[df['date'].isin([list(day_list)[i]])].copy()[['date', 'time', forecast_column_name]]
        x1 = np.zeros((len(copy1)))
        x2 = np.zeros((len(copy2)))

        for j in range(len(copy1)):
            x1[j] = copy1.loc[copy1.index[j], value_column_name]
            x2[j] = copy2.loc[copy2.index[j], forecast_column_name]

        mape_values = _calculate_mape(x1, x2)
        for j in range(len(copy1)):
            df.loc[copy1.index[j], 'MAPE'] = mape_values
    return np.array(df['MAPE'])


def rsquare(df: pd.DataFrame, value_column_name: str, forecast_column_name: str, datetime_column_name: str) -> np.ndarray:
    """
    Method for calculating R^2 for N-day dataframe

    :param df: user pandas dataframe (pd.DataFrame)
    :param value_column_name: name of real values column (str)
    :param forecast_column_name: name of forecast values column (str)
    :param datetime_column_name: name of datetime column (str)
    :return: numpy array with error values
    """
    df = df.copy(deep=True)
    df['R^2'] = r2_score(df[value_column_name], df[forecast_column_name])
    return np.array(df['R^2'])
