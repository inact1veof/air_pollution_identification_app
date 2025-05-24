"""
Air pollution forecasting class using SdaysAVR method
"""
import datetime
from typing import Union, List, Dict, Any
import numpy as np
import pandas as pd
from tqdm import tqdm
from .DayFunctions import (get_days, get_base_value, get_last_N_days_mean, get_last_day, get_N_days, get_correction, adjust)
from .dsm_timeseries import dsm_timeseries
from .BaseModel import BaseModel
import warnings


class SDaysAVR(BaseModel):
    """
    Forecasting air pollution by SdaysAVR method

    :param n_days: start from the N day
    """

    def __init__(self, n_days: int = 10):
        self._n_days = n_days
        self.day_list = None

    def _validate_dataframe(self, df: pd.DataFrame, datetime_column_name: str, value_column_name: str) -> None:
        """
        Method for checking data correctness

        :param df: pandas dataframe or dictionary list with datetime and value columns
        :param value_column_name: column name in df with float value of pollution
        :param datetime_column_name: column name in df with datetime value
        :return: None
        """

        if isinstance(df, pd.DataFrame):
            if datetime_column_name not in df.columns:
                raise ValueError(f"{datetime_column_name} not in dataframe.")
            elif value_column_name not in df.columns:
                raise ValueError(f"{value_column_name} not in dataframe.")

            if not pd.api.types.is_datetime64_any_dtype(df[datetime_column_name]):
                raise ValueError("Incorrect type of datetime column. Must be datetime.")
            elif not df[value_column_name].dtype == float:
                raise ValueError("Incorrect type of value column. Must be float.")

        self.df = df

    def _make_day_list(self, datetime_column_name: str, avg_day_flag: int):
        """
        Method for calculating day list of df

        :param datetime_column_name: column name in df with datetime value
        :return None
        """
        self.df['date'] = self.df[datetime_column_name].dt.date
        self.df['time'] = self.df[datetime_column_name].dt.time
        self.df = self.df.set_index(datetime_column_name)

        df_tmp = self.df.copy(deep=True)
        df_tmp = df_tmp.drop(columns=['time'])
        avg_day = df_tmp.groupby(['date']).sum()
        self.day_list = list(avg_day.index)
        if avg_day_flag == 1:
            return avg_day

    def predict(self, df: Union[pd.DataFrame, dsm_timeseries], day_points: int = None, datetime_column_name: str = None,
                value_column_name: str = None, method: str = "All"):
        """
        Predict method for use SDaysAVR

        :param df: pandas dataframe with datetime and value columns or DSM structure (pd.DataFrame, dsm_timeseries)
        :param value_column_name: column name in df with float value of pollution (str)
        :param datetime_column_name: column name in df with datetime value (str)
        :param day_points: count of value points for one day (int)
        :param method: method of forecasting (Only 1 last day = "Last", for full dataframe = "All")
        :return: numpy array with 1-day forecast (len == day_points) in "Last" method of forecasting, numpy array with
        N-day (df.shape[1] len) in "All" method of forecasting
        """
        warnings.filterwarnings("ignore")
        if isinstance(df, dsm_timeseries):
            data = df
            df = data.data
            datetime_column_name = data.time_column_name
            value_column_name = data.value_column_name
        # Validate dataframe
        df = df.copy(deep=True)
        self._validate_dataframe(df, datetime_column_name, value_column_name)
        avg_day = self._make_day_list(datetime_column_name, avg_day_flag=1)
        df = self.df
        df['forecast'] = float(0)

        # Forecast with method parameter
        if method == "All":
            for i in tqdm(range(self._n_days, len(self.day_list))):
                target_day = self.day_list[i]
                condition1 = get_days(target_day, self._n_days + 21)
                last_N_days_mean = get_last_N_days_mean(condition1, avg_day, value_column_name, n_days=self._n_days)
                condition2 = get_N_days(last_N_days_mean, condition1, avg_day, value_column_name, 0.5, n_days = self._n_days)
                b = get_base_value(df, condition2, value_column_name)
                c = get_last_day(df, condition2, value_column_name, day_points)
                a = get_correction(b, c,  value_column_name)
                b_adj = adjust(a, b)
                new_data = df[df['date'].isin([list(self.day_list)[i]])].copy()[['date', 'time', value_column_name]]
                for j in range(len(new_data)):
                    l = new_data.index[j]
                    if new_data.loc[l, 'time'] in list(b_adj.index):
                        tempData = b_adj.loc[b_adj.index == new_data.loc[l, 'time']]
                        df.loc[l, 'forecast'] = tempData.loc[tempData.index[0], value_column_name]
            return np.array(df['forecast'])
        elif method == "Last":
            target_day = self.day_list[-1] + datetime.timedelta(days=1)
            result = []
            try:
                condition1 = get_days(target_day, self._n_days + 21)
                last_N_days_mean = get_last_N_days_mean(condition1, avg_day, value_column_name, n_days=self._n_days)
                condition2 = get_N_days(last_N_days_mean, condition1, avg_day, value_column_name, 0.5,
                                        n_days=self._n_days)
                b = get_base_value(df, condition2, value_column_name)
                c = get_last_day(df, condition2, value_column_name, day_points)
                a = get_correction(b, c, value_column_name)
                b_adj = adjust(a, b)
                new_data = df[df['date'].isin([list(self.day_list)[-2]])].copy()[['date', 'time', value_column_name]]
                for j in range(len(new_data)):
                    l = new_data.index[j]
                    if new_data.loc[l, 'time'] in list(b_adj.index):
                        tempData = b_adj.loc[b_adj.index == new_data.loc[l, 'time']]
                        result.append(tempData.loc[tempData.index[0], value_column_name])
            except:
                raise ValueError("Incorrect size of input dataframe.")
            return np.array(result)
        else:
            raise ValueError("Incorrect method parameter. Must be 'All' or 'Last'.")
