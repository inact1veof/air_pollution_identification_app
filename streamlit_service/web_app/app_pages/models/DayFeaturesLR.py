"""
Air pollution forecasting class using Feature Extraction method for make regression
"""
import warnings
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import Union, List, Dict, Any
from .RLS import FilterRLS
from .dsm_timeseries import dsm_timeseries
from .BaseModel import BaseModel


class DayFeaturesLR(BaseModel):
    """
    Feature Extraction Linear Regressor Class

    :param rls_num_par: number of alfa for RLS model
    :param circles_count: number of circles of the data calculations
    :param *args: rls filter parameters
    :param *kwargs: rls filter parameters
    """

    def __init__(self, rls_num_par: int = 15, circles_count: int = 3, *args, **kwargs):
        self.rls_num_par = rls_num_par
        self.circles_count = circles_count
        self.day = 0
        self.days_number = 0
        self.df = None
        self.day_list = None
        self.day_points = 0
        self._features_number = 8
        self.w = None
        self.args = args
        self.kwargs = kwargs
        self.datetime_column_name = None
        self.value_column_name = None
        self.common_features_names = None

    def _validate_dataframe(self, df: pd.DataFrame, datetime_column_name: str,
                            value_column_name: str) -> None:
        """
        Method for checking data correctness

        :param df: pandas dataframe with datetime and value columns (pd.DataFrame)
        :param value_column_name: column name in df with float value of pollution (str)
        :param datetime_column_name: column name in df with datetime value (str)
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

    def _features_generation(self, is_predicting: bool = False) -> np.ndarray:
        """
        Method for extraction features array from timeseries using base data (value column) and common data (common columns)

        :return: np.ndarray
        """
        df = self.df
        circles_count = self.circles_count
        if not is_predicting:
            features_data = np.zeros((self._features_number + len(self.common_features_names), self.day_points,
                                      self.circles_count * len(self.day_list)))
        else:
            features_data = np.zeros((self._features_number + len(self.common_features_names), self.day_points, len(self.day_list)))
            circles_count = 1
        self.features_indexes = {}
        for item in self.common_features_names:
            self._features_number += 1
            self.features_indexes[item] = self._features_number
        for i in tqdm(range(circles_count * len(self.day_list))):
            pollution_sum = 0
            base_data = df[df['date'].isin([list(self.day_list)[i % len(self.day_list)]])].copy()[self.value_column_name]
            common_data = df[df['date'].isin([list(self.day_list)[i % len(self.day_list)]])].copy()[self.common_features_names]

            for j in range(min(len(base_data), self.day_points)):
                val = base_data.index[j]
                features_data[0, j, i] = base_data.loc[val]
                pollution_sum = pollution_sum + features_data[0, j, i]

                if j != 0:
                    if base_data.rolling(4).sum()[j] >= 0:
                        features_data[1, j, i] = base_data.rolling(4).sum()[j] / 4
                else:
                    features_data[1, j, i] = features_data[1, self.day_points - 1, i - 1]
                features_data[2, j, i] = base_data.index.weekday.isin([5, 6])[j] * 1

            temp_sum = 0
            pollution_sum = pollution_sum / self.day_points
            for j in range(self.day_points):
                if j % 4 == 0:
                    temp_sum = (features_data[0, j, i] + features_data[0, j + 1, i] + features_data[0, j + 2, i] +
                                features_data[0, j + 3, i]) / 4
                features_data[3, j, i] = temp_sum
                if pollution_sum > 0:
                    features_data[4, j, i] = features_data[0, j, i] / pollution_sum

            for j in range(self.day_points):
                if j > 3:
                    features_data[5, j, i] = features_data[3, j, i] - features_data[3, j - 4, i]
                else:
                    features_data[5, j, i] = features_data[3, j, i] - features_data[3, self.day_points - 1, i - 1]

            for j in range(self.day_points):
                if features_data[0, j, i] > (pollution_sum * 0.2):
                    features_data[6, j, i] = 1
                else:
                    features_data[6, j, i] = 0
            for j in range(self.day_points):
                if features_data[0, j, i] > (pollution_sum * 1.5):
                    features_data[7, j, i] = 1
                else:
                    features_data[7, j, i] = 0
            for item in self.common_features_names:
                for j in range(self.day_points):
                    try:
                        index = common_data[item].index[j]
                    except:
                        index = -1
                    if index != -1:
                        features_data[self.features_indexes[item] - 1, j, i] = common_data.loc[index, item]
                    else:
                        features_data[self.features_indexes[item] - 1, j, i] = common_data[item].mean()

        return features_data

    def fit(self, df: Union[pd.DataFrame, dsm_timeseries], day_points: int, datetime_column_name: str = None,
            value_column_name: str = None, common_features_names: List[str] = None) -> None:
        """
        Fit method for calculating weights

        :param df: pandas dataframe with datetime and value columns or DSM structure (pd.DataFrame, dsm_timeseries)
        :param value_column_name: column name in df with float value of pollution (str)
        :param datetime_column_name: column name in df with datetime value (str)
        :param day_points: count of value points for one day (int)
        :param common_features_names: names of common features in df (int)
        :return None
        """
        warnings.filterwarnings("ignore")
        if isinstance(df, dsm_timeseries):
            data = df
            df = data.data
            datetime_column_name = data.time_column_name
            value_column_name = data.value_column_name
        if common_features_names is None:
            common_features_names = []
        # Validate Dataframe
        self._validate_dataframe(df, datetime_column_name, value_column_name)

        # Make forecast parameters
        self._make_day_list(datetime_column_name)
        self.day_points = day_points
        self.common_features_names = common_features_names
        self.datetime_column_name = datetime_column_name
        self.value_column_name = value_column_name

        self.rls_num_par = self.rls_num_par + (len(common_features_names)* 2)

        y_estimate = np.zeros((self.day_points, self.circles_count * len(self.day_list)))
        w = np.zeros((self.day_points, self.rls_num_par))
        w_list = np.zeros((self.circles_count * len(self.day_list) * self.day_points, self.rls_num_par))

        # First loop of data calculation
        features_data = self._features_generation()

        rls_model = FilterRLS(self.rls_num_par, *self.args, **self.kwargs)

        # Second loop of data calculation
        for m in range(self.circles_count):  # multiple passes through the same data
            for s in range(0, len(self.day_list)):  # for each available day in the data
                y_before = np.zeros((day_points, self.rls_num_par))
                for t in range(day_points):
                    day = self.day
                    if day > 7:
                        base_data = [features_data[0, t, day - 1], features_data[0, t, day - 7],
                                          features_data[1, t, day - 1], features_data[1, t, day - 7],
                                          features_data[2, t, day],
                                          features_data[3, t, day - 1], features_data[3, t, day - 7],
                                          features_data[4, t, day - 1], features_data[4, t, day - 7],
                                          features_data[5, t, day - 1], features_data[5, t, day - 7],
                                          features_data[6, t, day - 1], features_data[6, t, day - 7],
                                          features_data[7, t, day - 1], features_data[7, t, day - 7]]
                        for item in self.features_indexes:
                            base_data.append(features_data[self.features_indexes[item] - 1, t, day - 1])
                            base_data.append(features_data[self.features_indexes[item] - 1, t, day - 7])

                        y_before[t, :] = base_data


                    y_estimate[t, day] = np.dot(w[t], y_before[t, :].T)

                    if y_estimate[t, day] > 1.5 * np.max(features_data[0, t, day - 1]):
                        y_estimate[t, day] = 1.5 * np.max(features_data[0, t, day - 1])
                    else:
                        if y_estimate[t, day] < 0:
                            y_estimate[t, day] = 0

                    w_list[self.day_points * day + t] = w[t]

                y, e, w = rls_model.run(features_data[0, :, self.day], y_before)
                self.day += 1
                self.w = w

    def predict(self, X: Union[pd.DataFrame, dsm_timeseries], method: str = "All") -> np.ndarray:
        """
        Method for make predict

        :param X: array of features for making regression (pd.DataFrame) one week or DSM structure
        :param method: method of forecasting (Only 1 last day = "Last", for full dataframe = "All") (str)
        :return: array of forecasts (np.array)
        """
        if isinstance(X, dsm_timeseries):
            df = X.data
        else:
            df = X
        self.df = df
        if method == "All":
            self.day = 0
            self._validate_dataframe(df, self.datetime_column_name, self.value_column_name)
            self._make_day_list(self.datetime_column_name)
            features_data = self._features_generation()
            y_before = np.zeros((self.day_points, self.rls_num_par))
            y_estimate = np.zeros((self.day_points, self.circles_count * len(self.day_list)))
            self.df['forecast'] = 0
            for _ in range(self.circles_count):
                for s in range(0, len(self.day_list)):
                    for t in range(self.day_points):
                        day = self.day
                        if day > 7:
                            base_data = [features_data[0, t, day - 1], features_data[0, t, day - 7],
                                                  features_data[1, t, day - 1], features_data[1, t, day - 7],
                                                  features_data[2, t, day],
                                                  features_data[3, t, day - 1], features_data[3, t, day - 7],
                                                  features_data[4, t, day - 1], features_data[4, t, day - 7],
                                                  features_data[5, t, day - 1], features_data[5, t, day - 7],
                                                  features_data[6, t, day - 1], features_data[6, t, day - 7],
                                                  features_data[7, t, day - 1], features_data[7, t, day - 7]]

                            for item in self.features_indexes:
                                base_data.append(features_data[self.features_indexes[item] - 1, t, day - 1])
                                base_data.append(features_data[self.features_indexes[item] - 1, t, day - 7])

                            y_before[t, :] = base_data


                        y_estimate[t, day] = np.dot(self.w[t], y_before[t, :].T)

                        if y_estimate[t, day] > 1.5 * np.max(features_data[0, t, day - 1]):
                            y_estimate[t, day] = 1.5 * np.max(features_data[0, t, day - 1])
                        else:
                            if y_estimate[t, day] < 0:
                                y_estimate[t, day] = 0
                    self.day += 1
            for i in tqdm(range(len(self.day_list))):
                copy_to_data = self.df[self.df['date'].isin([list(self.day_list)[i]])].copy()[['date','time', self.value_column_name]]
                for j in range(len(copy_to_data)):
                    l = copy_to_data.index[j]
                    self.df.loc[l, 'forecast'] = float(y_estimate[j,i+(self.circles_count-1)*len(self.day_list)])
            return np.array(self.df['forecast'])
        if method == "Last":
            self._validate_dataframe(df, self.datetime_column_name, self.value_column_name)
            self._make_day_list(self.datetime_column_name)

            last_day = self.day_list[-1]
            next_day = last_day + pd.Timedelta(days=1)
            is_weekend = 1 if next_day.weekday() in [5, 6] else 0
            self.day_list = self.day_list[-7:]
            features_data = self._features_generation(is_predicting=True)
            y_before = np.zeros((self.day_points, self.rls_num_par))
            y_estimate = np.zeros((self.day_points, 1))
            for t in range(self.day_points):
                day = len(self.day_list)
                if day >= 7:
                    base_data = [features_data[0, t, day - 1], features_data[0, t, day - 7],
                                 features_data[1, t, day - 1], features_data[1, t, day - 7],
                                 is_weekend,
                                 features_data[3, t, day - 1], features_data[3, t, day - 7],
                                 features_data[4, t, day - 1], features_data[4, t, day - 7],
                                 features_data[5, t, day - 1], features_data[5, t, day - 7],
                                 features_data[6, t, day - 1], features_data[6, t, day - 7],
                                 features_data[7, t, day - 1], features_data[7, t, day - 7]]

                    for item in self.features_indexes:
                        base_data.append(features_data[self.features_indexes[item] - 1, t, day - 1])
                        base_data.append(features_data[self.features_indexes[item] - 1, t, day - 7])

                    y_before[t, :] = base_data

                y_estimate[t, 0] = np.dot(self.w[t], y_before[t, :].T)

                if y_estimate[t, 0] > 1.5 * np.max(features_data[0, t, day - 1]):
                    y_estimate[t, 0] = 1.5 * np.max(features_data[0, t, day - 1])
                elif y_estimate[t, 0] < 0:
                    y_estimate[t, 0] = 0

            return y_estimate.flatten()
        else:
            raise ValueError("Incorrect size of input dataframe.")
