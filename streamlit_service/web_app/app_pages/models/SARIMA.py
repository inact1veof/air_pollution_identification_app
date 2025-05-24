"""
Air pollution forecasting class using SARIMA method
"""
from scipy.optimize import minimize
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
import pandas as pd
import statsmodels.api as sm
from tqdm import tqdm
from typing import Union, List, Dict, Any
from .BaseModel import BaseModel
import statsmodels.api as sm
from .dsm_timeseries import dsm_timeseries


class SARIMA(BaseModel):
    """
    SARIMA model class

    :param p: The p lag has significant autocorrelation by PACF (int)
    :param d: Differentiated once (int)
    :param q: The q lag has significant autocorrelation by ACF (int)
    :param P: PACF positive by first lag (int)
    :param D: Seasonality (1-yes, 0 - no)(int)
    :param Q: ACF positive by first lag (int)
    """
    def __init__(self, p: int = 1, d: int = 1, q: int = 1, P: int = 1, D: int = 1, Q: int = 1):
        self.p = p
        self.d = d
        self.q = q
        self.P = P
        self.D = D
        self.Q = Q
        self.model = None
        self.fit_forecast = None
        self.df = None
        self.day_points = None

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

    def _make_day_list(self, datetime_column_name: str, avg_day_flag: int = 1):
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

    def fit(self, df: Union[pd.DataFrame, dsm_timeseries], start_day: int, day_points: int, datetime_column_name: str=None,
            value_column_name: str = None) -> None:
        """
        Fit method for using Sarimax statsmodels

        :param df: pandas dataframe with datetime and value columns or DSM structure (pd.DataFrame, dsm_timeseries)
        :param start_day: starting day for making forecast (int)
        :param value_column_name: column name in df with float value of pollution (str)
        :param datetime_column_name: column name in df with datetime value (str)
        :param day_points: count of value points for one day (int)
        :return None
        """
        if isinstance(df, dsm_timeseries):
            data = df
            df = data.data
            datetime_column_name = data.time_column_name
            value_column_name = data.value_column_name
            # Validate dataframe
        self.df = df
        df = df.copy(deep=True)
        df['forecast'] = float(0)
        self._validate_dataframe(df, datetime_column_name, value_column_name)
        self._make_day_list(datetime_column_name)
        self.day_points = day_points
        for i in tqdm(range(start_day, len(self.day_list))):
            temp = pd.DataFrame(df[value_column_name][(i - day_points) * day_points:(i - 1) * day_points])

            model = sm.tsa.statespace.SARIMAX(temp[value_column_name], order=(self.p, self.d, self.q), seasonal_order=(self.P, self.D, self.Q, day_points),enforce_stationarity=False).fit(disp=-1)
            self.model = model

            pred_data = model.predict(len(temp), len(temp) + day_points, dynamic=True)
            copy_to_data = df[df['date'].isin([list(self.day_list)[i]])].copy()[['date', 'time', value_column_name]]

            for j in range(0, len(copy_to_data)):
                l = copy_to_data.index[j]
                if pred_data.iloc[j] > 0:
                    df.loc[l, 'forecast'] = pred_data.iloc[j]

            self.fit_forecast = np.array(df['forecast'])



    def predict(self, method: str = "All") -> np.ndarray:
        """
        Method for make predict

        :param method: method of forecasting (Only 1 last day = "Last", for full dataframe = "All") (str)
        :return: array of forecasts (np.array)
        """
        if method == 'All':
            return self.fit_forecast
        elif method == 'Last':
            model = self.model
            pred_data = model.predict(len(self.df), len(self.df)+ self.day_points, dynamic=True)
            return np.array(pred_data)
        else:
            raise ValueError("Incorrect method parameter. Must be 'All' or 'Last'.")