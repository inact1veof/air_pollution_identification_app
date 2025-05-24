import datetime
import pandas as pd
import numpy as np


def n_previous_days(date, n):
    """
    Method for make generator for N previous same dates

    :param date: current date
    :param n: count of days
    :return: yield generator, list of previous N days
    """
    td = datetime.timedelta(days=1)
    for i in range(1, n + 1):
        date = date - td  # N times we take one week ago day [date-1 week, date-2 weeks, date-3 weeks ... etc]
        yield date


def get_days(target_day, n):
    """
    Returns an array with N dates - N previous same days (for example, three previous mondays)

    :param target_day: day for forecasting
    :param n: count of previous same days
    :return: list of datetime objects
    """
    days = []
    for day in n_previous_days(target_day, n):
        days.append(day)
    return days


def get_NSP_days(condition, n_days):
    """
    Returns an array with

    :param condition: result of get_days - N previous same days
    :param n_days: count of concrete days
    :return: list of concrete days
    """
    some_days = []
    for i in range(n_days):
        some_days.append(
            condition[i * 7 + 6])
        if len(some_days) >= n_days:
            return some_days
    return some_days


def get_base_value(df, condition, value_column, date_column='date', time_column='time'):
    """
    Method for take mean of N previous days values from df

    :param df: pandas dataframe with datetime and value columns (pd.DataFrame)
    :param condition: list of previous days (List)
    :param date_column: name of df date column (str)
    :param value_column: name of df value column (str)
    :param time_column: name of df time column (str)
    :return: grouped df with mean values
    """
    df_tmp = df.copy(deep=True)  # we take the values of these days
    fitting_days_values = df_tmp[df_tmp['date'].isin(condition)].copy()[['date', 'time', value_column]]
    fitting_days_values = fitting_days_values.drop(columns=['date'])
    return fitting_days_values.groupby([time_column]).mean()


def get_last_N_days_mean(condition, avg_day, column, n_days):
    """
    Method for calculating mean value of N last days

    :param condition: array of days
    :param avg_day: grouped by date array of days
    :param column: value column in df
    :param n_days: count of n last days
    :return: array of average values
    """
    last_N_days = []

    for day in condition:
        if day in avg_day.index:
            last_N_days.append(day)
            if len(last_N_days) == n_days:
                break
    return avg_day[column][last_N_days].mean()


def get_N_days(last_N_days_mean, condition, avg_day, column, value, n_days):
    """
    Methods return values of last N days

    :param last_N_days_mean: mean values of last N days
    :param condition: array of days
    :param avg_day: grouped by date array of days
    :param column: value column in df
    :param value: threshold
    :param n_days: count of n last days
    :return: array of values
    """
    some_days = []
    for day in condition:
        if day in avg_day.index:
            if avg_day[column][day] >= last_N_days_mean * value:
                some_days.append(day)
        if len(some_days) >= n_days:
            return some_days
    return some_days


def get_last_day(df, condition2, value_column_name, day_points):
    """
    Methods return only previous day values

    :param df: user pandas dataframe
    :param condition2: array of days
    :param value_column_name: value column in df
    :param day_points: count points in a day
    :return: array of values of previous day
    """
    temp = pd.DataFrame()
    for i in range(len(condition2)):
        temp = df[df['date'].isin([condition2[i]])].copy()[['date', 'time', value_column_name]]
        if len(temp) == day_points:
            break
    return temp.groupby(['time']).agg({value_column_name: 'mean'}).reset_index()


def get_correction(b, c, value_column_name):
    """
    TODO: дописать описание

    :param b:
    :param c:
    :param value_column_name: value column in df
    :return: correction values array
    """
    a_1 = np.mean(c[value_column_name]) - np.mean(b[value_column_name])
    a_2 = np.mean(c[value_column_name]) - np.mean(b[value_column_name])
    return (a_1 + a_2) / 2


def adjust(a, b):
    """
    TODO: коррекция сглаживания с усредненным

    :param a:
    :param b:
    :return:
    """
    b_adj = b + a
    b_high = b * 1.2
    b_low = b * 0.8
    flag = b_adj > b_high
    b_adj[flag] = b_high[flag]
    flag = b_adj < b_low
    b_adj[flag] = b_low[flag]
    return b_adj
