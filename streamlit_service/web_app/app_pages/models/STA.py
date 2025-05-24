"""
Air pollution forecasting class using STA Method
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


class STA(BaseModel):
    """
        STA LR forecasting method Class

        :param rls_num_par: number of alfa for RLS model
        :param circles_count: number of circles of the data calculations
        :param *args: rls filter parameters
        :param *kwargs: rls filter parameters
        """

    def __init__(self, rls_num_par: int = 4, circles_count: int = 1, *args, **kwargs):
        self.rls_num_par = rls_num_par
        self.circles_count = circles_count
        self.day = 0
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
        self.y_estimate = None

    def _validate_dataframe(self, df: pd.DataFrame, datetime_column_name: str, value_column_name: str) -> None:
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

        :param datetime_column_name: column name in df with datetime value (str)
        :return None
        """

        self.df['date'] = self.df[datetime_column_name].dt.date
        self.df['time'] = self.df[datetime_column_name].dt.time
        self.df = self.df.set_index(datetime_column_name)

        df_tmp = self.df.copy(deep=True)
        df_tmp = df_tmp.drop(columns=['time'])

        avg_day = df_tmp.groupby(['date']).sum()
        self.day_list = list(avg_day.index)

    def _make_base_features(self, common_features_names):
        """
        Method for extraction base features array from timeseries using base data (value column) and common data (common columns)

        :param common_features_names: list of column names in df of common features
        :return: np.ndarray of timeseries data and np.ndarray common features
        """
        main_data = np.zeros((self.day_points, self.circles_count * len(self.day_list)))
        common_data = np.zeros((len(common_features_names), self.day_points, len(self.day_list)))
        for i in tqdm(range(self.circles_count * len(self.day_list))):
            copy_from_data = self.df[self.df['date'].isin([list(self.day_list)[i % len(self.day_list)]])].copy()[
                [self.value_column_name]]
            for j in range(min(len(copy_from_data), self.day_points)):
                l = copy_from_data.index[j]
                # l is the index of the instance (%d.%m.%Y %H:%M:%S)
                main_data[j, i] = copy_from_data.loc[l, self.value_column_name]

        for common_feature_index in range(0, len(common_features_names)):
            for val in range(len(self.day_list)):
                values = self.df[self.df['date'].isin([self.day_list[val]])][
                    [common_features_names[common_feature_index]]]
                if len(values) == self.day_points:
                    common_data[common_feature_index, :, val] = values[common_features_names[common_feature_index]]
                else:
                    temp_data = np.pad(values[common_features_names[common_feature_index]],
                                       (0, self.day_points - len(values[common_features_names[common_feature_index]])),
                                       'constant', constant_values=0)
                    common_data[common_feature_index, :, val] = temp_data
        return main_data, common_data

    def _make_fit(self, main_data, common_data, common_features_names, method_features_count, rls_model):
        """
        Method for fit on advanced features array from base data

        :param main_data: np.array with timeseries values
        :param common_data: np.array with common features values
        :param common_features_names: list of column names in df of common features
        :param method_features_count: rls_num_par
        :param rls_model: RLS filter model
        :return: np.ndarray of predict data
        """
        y_estimate = np.zeros((self.day_points, self.circles_count * len(self.day_list)))
        average = np.zeros((self.day_points, self.circles_count * len(self.day_list)))
        y_before = np.zeros((self.day_points, self.rls_num_par + len(common_features_names)))
        day = 0
        for m in tqdm(range(self.circles_count)):  # multiple passes through the same data
            for s in range(0, len(self.day_list)):  # for each available day in the data

                for t in range(self.day_points):
                    diff_n = t - self.rls_num_par
                    average[t, day] = 0  # Computing average of last three similar days of the same interval
                    if day >= 28:
                        average[t, day] = (main_data[t, day - 7] + main_data[t, day - 14] + main_data[t, day - 21] +
                                           main_data[t, day - 28]) / 4
                    else:
                        if (day > 0) & (day < 28):
                            average[t, day] = main_data[t, day - 1]

                    if diff_n == -3:  # Creating the vector of previous estimates
                        features = [main_data[self.day_points - 1, day - 1], main_data[self.day_points - 2, day - 1],
                                    main_data[self.day_points - 3, day - 1], average[t, day]]
                        features.extend([0] * len(common_features_names))
                        y_before[t, :] = features
                    else:
                        if diff_n == -2:
                            features = [y_estimate[0, day], main_data[self.day_points - 1, day - 1],
                                        main_data[self.day_points - 2, day - 1],
                                        average[t, day]]
                            features.extend([0] * len(common_features_names))
                            y_before[t, :] = features
                        else:
                            if diff_n == -1:
                                features = [y_estimate[1, day], y_estimate[0, day],
                                            main_data[self.day_points - 1, day - 1],
                                            average[t, day]]
                                features.extend([0] * len(common_features_names))
                                y_before[t, :] = features
                            else:
                                features = [y_estimate[t - 1, day], y_estimate[t - 2, day],
                                            y_estimate[t - 3, day], average[t, day]]
                                features.extend([0] * len(common_features_names))
                                y_before[t, :] = features
                    for i in range(0, len(common_features_names)):
                        y_before[:, method_features_count + i + 1] = common_data[i, :, s]
                    if np.any(np.abs(self.w) > 0.15):
                        self.w = np.clip(self.w, 0.25, 0.5)
                    y_estimate[t, day] = np.dot(self.w[t], y_before[t, :].T)

                    if y_estimate[t, day] > self.df[self.value_column_name].max() * 1.2:
                        y_estimate[t, day] = self.df[self.value_column_name].max() * 1.2
                    else:
                        if y_estimate[t, day] < 0:
                            y_estimate[t, day] = 0
                y, e, w = rls_model.run(main_data[:, day], y_before)
                self.w = w
                day = day + 1
        self.y_estimate = y_estimate

    def fit(self, df: Union[pd.DataFrame, dsm_timeseries], day_points: int, datetime_column_name: str=None,
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
        self._make_day_list(datetime_column_name)
        self.day_points = day_points
        self.value_column_name = value_column_name
        self.datetime_column_name = datetime_column_name
        self.common_features_names = common_features_names

        method_features_count = 4
        w = np.zeros((self.day_points, method_features_count + len(common_features_names)))
        self.w = w

        main_data, common_data = self._make_base_features(common_features_names)

        rls_model = FilterRLS(self.rls_num_par + len(common_features_names), *self.args, **self.kwargs)

        self._make_fit(main_data, common_data, common_features_names, method_features_count, rls_model)

    def predict(self, method: str = "All") -> np.ndarray:
        """
        Method for make predict

        :param method: method of forecasting (Only 1 last day = "Last", for full dataframe = "All") (str)
        :return: array of forecasts (np.array)
        """
        if method == "All":
            for i in tqdm(range(len(self.day_list))):
                copy_to_data = self.df[self.df['date'].isin([list(self.day_list)[i]])].copy()[
                    ['date', 'time', self.value_column_name]]
                for j in range(min(len(copy_to_data), self.day_points)):
                    l = copy_to_data.index[j]
                    self.df.loc[l, 'forecast'] = float(
                        self.y_estimate[j, i + (self.circles_count - 1) * len(self.day_list)])
            return np.array(self.df['forecast'])

        if method == "Last":
            self.day_list.append(self.day_list[-1] + timedelta(days=1))
            main_data, common_data = self._make_base_features(self.common_features_names)
            rls_model = FilterRLS(self.rls_num_par + len(self.common_features_names), *self.args, **self.kwargs)
            self._make_fit(main_data, common_data, self.common_features_names, 4, rls_model)
            for i in tqdm(range(len(self.day_list))):
                copy_to_data = self.df[self.df['date'].isin([list(self.day_list)[i]])].copy()[
                    ['date', 'time', self.value_column_name]]
                for j in range(min(len(copy_to_data), self.day_points)):
                    l = copy_to_data.index[j]
                    self.df.loc[l, 'forecast'] = float(
                        self.y_estimate[j, i + (self.circles_count - 1) * len(self.day_list)])
            result = self.df.tail(self.day_points)
            return np.array(result['forecast'])
        else:
            raise ValueError("Incorrect size of input dataframe.")
