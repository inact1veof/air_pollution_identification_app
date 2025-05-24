"""
Air pollution forecasting class using Holt-Winters algorithm
"""
from scipy.optimize import minimize
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
from tqdm import tqdm
from typing import Union, List, Dict, Any
from .BaseModel import BaseModel
from .dsm_timeseries import dsm_timeseries


class HW(BaseModel):
    class HW_core:
        def __init__(self, series, slen, alpha, beta, gamma, n_preds, scaling_factor=1.96):
            self.series = series
            self.slen = slen
            self.alpha = alpha
            self.beta = beta
            self.gamma = gamma
            self.n_preds = n_preds
            self.scaling_factor = scaling_factor

        def initial_trend(self):
            sum = 0.0
            for i in range(self.slen):
                try:
                    sum += float(self.series[i + self.slen] - self.series[i]) / self.slen
                except:
                    sum += 0
            return sum / self.slen

        def initial_seasonal_components(self):
            seasonals = {}
            season_averages = []

            n_seasons = int(len(self.series) / self.slen)
            for j in range(n_seasons):
                season_averages.append(sum(self.series[self.slen * j:self.slen * j + self.slen]) / float(self.slen))
            for i in range(self.slen):
                self.series = np.array(self.series)
                sum_of_vals_over_avg = 0.0
                for j in range(n_seasons):
                    idx = self.slen * j + i
                    sum_of_vals_over_avg += self.series[idx] - season_averages[j]
                seasonals[i] = sum_of_vals_over_avg / n_seasons
            return seasonals

        def triple_exponential_smoothing(self):
            self.result = []
            self.Smooth = []
            self.Season = []
            self.Trend = []
            self.PredictedDeviation = []
            self.UpperBond = []
            self.LowerBond = []

            seasonals = self.initial_seasonal_components()

            for i in range(len(self.series) + self.n_preds):
                if i == 0:
                    smooth = self.series[0]
                    trend = self.initial_trend()
                    self.result.append(self.series[0])
                    self.Smooth.append(smooth)
                    self.Trend.append(trend)
                    self.Season.append(seasonals[i % self.slen])
                    self.PredictedDeviation.append(0)
                    self.UpperBond.append(self.result[0] + self.scaling_factor * self.PredictedDeviation[0])
                    self.LowerBond.append(self.result[0] - self.scaling_factor * self.PredictedDeviation[0])
                    continue
                if i >= len(self.series):
                    m = i - len(self.series) + 1
                    self.result.append((smooth + m * trend) + seasonals[i % self.slen])
                    self.PredictedDeviation.append(self.PredictedDeviation[-1] * 1.01)
                else:
                    val = self.series[i]
                    last_smooth, smooth = smooth, self.alpha * (val - seasonals[i % self.slen]) + (1 - self.alpha) * (
                            smooth + trend)
                    trend = self.beta * (smooth - last_smooth) + (1 - self.beta) * trend
                    seasonals[i % self.slen] = self.gamma * (val - smooth) + (1 - self.gamma) * seasonals[i % self.slen]
                    self.result.append(smooth + trend + seasonals[i % self.slen])
                    self.PredictedDeviation.append(
                        self.gamma * np.abs(self.series[i] - self.result[i]) + (1 - self.gamma) *
                        self.PredictedDeviation[-1])
                self.UpperBond.append(self.result[-1] + self.scaling_factor * self.PredictedDeviation[-1])
                self.LowerBond.append(self.result[-1] - self.scaling_factor * self.PredictedDeviation[-1])
                self.Smooth.append(smooth)
                self.Trend.append(trend)
                self.Season.append(seasonals[i % self.slen])

    """
    Holt-Winters model class

    :param slen: season lenght (int)
    :param alpha: HW model param (float)
    :param beta: HW model param (float)
    :param gamma: HW model param (float)
    :param scaling_factor: sets the width of the Brutlag confidence interval (usually takes values from 2 to 3) (float)
    """

    def __init__(self, alpha: float = 0, beta: float = 0, gamma: float = 0, scaling_factor: float = 2.56):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.scaling_factor = scaling_factor
        self.model = None
        self.df = None

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

    def _make_day_list(self, datetime_column_name: str):
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

    def __timeseriesCVscore(self, x, data):
        errors = []
        values = data.values
        alpha, beta, gamma = x
        tscv = TimeSeriesSplit(n_splits=2)
        for train, test in tscv.split(values):
            model = self.HW_core(series=values[train], slen=24, alpha=alpha, beta=beta, gamma=gamma, n_preds=len(test))
            model.triple_exponential_smoothing()
            predictions = model.result[-len(test):]
            actual = values[test]
            error = mean_squared_error(predictions, actual)
            errors.append(error)
        return np.mean(np.array(errors))

    def predict(self, df: Union[pd.DataFrame, dsm_timeseries], start_day: int = 14, day_points: int = 72,
                datetime_column_name: str = None,
                value_column_name: str = None, method: str = "All") -> np.ndarray:
        """
        Predict method for use HW

        :param df: pandas dataframe with datetime and value columns or DSM structure (pd.DataFrame, dsm_timeseries)
        :param start_day: starting day of forecast (int)
        :param value_column_name: column name in df with float value of pollution (str)
        :param datetime_column_name: column name in df with datetime value (str)
        :param day_points: count of value points for one day (int)
        :param method: method of forecasting (Only 1 last day = "Last", for full dataframe = "All")
        :return: numpy array with 1-day forecast (len == day_points) in "Last" method of forecasting, numpy array with
        N-day (df.shape[1] len) in "All" method of forecasting
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

        e_list = []

        if method == "All":
            for k in tqdm(range(start_day, len(self.day_list))):
                data = df[value_column_name][(k - start_day) * day_points:(k - 1) * day_points]
                if (k % 7 == 0):
                    x = [self.alpha, self.beta, self.gamma]
                    opt = minimize(self.__timeseriesCVscore, x0=x, args=data, method="TNC", bounds=(
                        (0, 1), (0, 1), (0, 1)))
                    self.alpha, self.beta, self.gamma = opt.x
                    e_list.append(self.alpha)
                model = self.HW_core(data, slen=day_points, alpha=self.alpha, beta=self.beta, gamma=self.gamma,
                                     n_preds=day_points, scaling_factor=2.56)
                model.triple_exponential_smoothing()
                copy_to_data = df[df['date'].isin([list(self.day_list)[k]])].copy()[['date', 'time', value_column_name]]
                for j in range(len(copy_to_data)):
                    l = copy_to_data.index[j]
                    try:
                        if model.result[(start_day - 1) * day_points + j] > 0:
                            df.loc[l, 'forecast'] = model.result[(start_day - 1) * day_points + j]
                    except:
                        try:
                            if model.result[(start_day - 7) * day_points + j] > 0:
                                df.loc[l, 'forecast'] = model.result[(start_day - 7) * day_points + j]
                        except:
                            if len(model.result) - 1 < (start_day - 7) * day_points + j:
                                df.loc[l, 'forecast'] = 0
                            elif model.result[((start_day - 7) * day_points + j) - 1] > 0:
                                df.loc[l, 'forecast'] = model.result[((start_day - 7) * day_points + j) - 1]
            return np.array(df['forecast'])
        elif method == "Last":
            last_date = df[datetime_column_name].max()
            next_day = last_date + pd.Timedelta(days=1)

            data = df[value_column_name][-day_points*start_day:]

            x = [self.alpha, self.beta, self.gamma]
            opt = minimize(self.__timeseriesCVscore, x0=x, args=data, method="TNC", bounds=(
                (0, 1), (0, 1), (0, 1)))
            self.alpha, self.beta, self.gamma = opt.x
            e_list.append(self.alpha)

            model = self.HW_core(data, slen=day_points, alpha=self.alpha, beta=self.beta, gamma=self.gamma,
                                 n_preds=day_points, scaling_factor=2.56)
            model.triple_exponential_smoothing()

            forecast = []
            for j in range(day_points):
                forecast.append(model.result[j] if model.result[j] > 0 else 0)
            return np.array(forecast)
        else:
            raise ValueError("Incorrect method parameter. Must be 'All' or 'Last'.")


def timeseriesCVscore(x, data):
    errors = []
    values = data.values
    alpha, beta, gamma = x
    tscv = TimeSeriesSplit(n_splits=2)
    for train, test in tscv.split(values):
        model = HW(slen=24, alpha=alpha, beta=beta, gamma=gamma)
        model._triple_exponential_smoothing(values[train], len(test))
        predictions = model.result[-len(test):]
        actual = values[test]
        error = mean_squared_error(predictions, actual)
        errors.append(error)
    return np.mean(np.array(errors))
