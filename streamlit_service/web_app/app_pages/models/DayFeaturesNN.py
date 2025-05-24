"""
Air pollution forecasting class using Feature Extraction method for make neural network predict
"""
import warnings
from datetime import datetime, timedelta
from tabnanny import verbose

import numpy as np
import pandas as pd
from numpy import ndarray, dtype, floating, float_
from numpy._typing import _64Bit
from tqdm import tqdm
from typing import Union, List, Dict, Any, Tuple
from .dsm_timeseries import dsm_timeseries

from .BaseModel import BaseModel
from keras.callbacks import ModelCheckpoint
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten


class DayFeaturesNN(BaseModel):
    """
    Feature Extraction NN Regressor Class

    :param num_par: number of alfa for NN model
    :param circles_count: number of circles of the data calculations
    :param *args: neural network parameters
    :param *kwargs: count of neural network parameters
    """

    def __init__(self, num_par: int = 15, circles_count: int = 1, *args, **kwargs):
        self.num_par = num_par
        self.circles_count = circles_count
        self.day = 0
        self.days_number = 0
        self.df = None
        self.day_list = None
        self.day_points = 0
        self._features_number = 8
        self.NN_model = None
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

    @staticmethod
    def _normalize(xi, xmin, xmax):
        """
        Method for using normalization

        :param xi: current value (float)
        :param xmin: minimal value of this day
        :param xmax: maximum value of this day
        """
        norm = (xi - xmin) / (xmax - xmin)
        return norm

    def _features_generation(self, is_predicting=False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Method for extraction features array from timeseries using base data (value column) and common data (common columns)

        :return: np.ndarray, np.ndarray, np.ndarray
        """
        df = self.df
        circles_count = self.circles_count
        if not is_predicting:
            features_data = np.zeros((self._features_number + len(self.common_features_names), self.day_points,
                                      self.circles_count * len(self.day_list)))
            min_max_features_data = np.zeros((self._features_number + len(self.common_features_names), 2))
        else:
            features_data = np.zeros((self._features_number, self.day_points, len(self.day_list)+1))
            min_max_features_data = np.zeros((self._features_number, 2))
            circles_count = 1


        data_target = np.zeros((self.day_points * len(self.day_list), 1))
        if not is_predicting:
            self.features_indexes = {}
            for item in self.common_features_names:
                self._features_number += 1
                self.features_indexes[item] = self._features_number

        for i in range(circles_count * len(self.day_list)):
            base_data = df[df['date'].isin([list(self.day_list)[i % len(self.day_list)]])].copy()[self.value_column_name]
            common_data = df[df['date'].isin([list(self.day_list)[i % len(self.day_list)]])].copy()[self.common_features_names]
            sum_LOAD = 0

            for j in range(min(self.day_points, len(base_data.index))):
                l = base_data.index[j]
                features_data[0, j, i] = base_data.loc[l]
                data_target[i * self.day_points + j] = features_data[0, j, i]

                sum_LOAD = sum_LOAD + features_data[0, j, i]

                if j != 0:
                    if base_data.rolling(4).sum()[j] >= 0:
                        features_data[1, j, i] = base_data.rolling(4).sum()[j] / 4
                else:
                    features_data[1, j, i] = features_data[1, self.day_points - 1, i - 1]

                features_data[2, j, i] = base_data.index.weekday.isin([5, 6])[j] * 1

                if min_max_features_data[0, 0] > features_data[0, j, i]:
                    min_max_features_data[0, 0] = features_data[0, j, i]
                if min_max_features_data[0, 1] < features_data[0, j, i]:
                    min_max_features_data[0, 1] = features_data[0, j, i]

                if min_max_features_data[1, 0] > features_data[1, j, i]:
                    min_max_features_data[1, 0] = features_data[1, j, i]
                if min_max_features_data[1, 1] < features_data[1, j, i]:
                    min_max_features_data[1, 1] = features_data[1, j, i]

                if min_max_features_data[2, 0] > features_data[2, j, i]:
                    min_max_features_data[2, 0] = features_data[2, j, i]
                if min_max_features_data[2, 1] < features_data[2, j, i]:
                    min_max_features_data[2, 1] = features_data[2, j, i]

            temp_sum = 0
            sum_LOAD = sum_LOAD / self.day_points

            for j in range(min(self.day_points, len(base_data.index))):
                if j % 4 == 0:
                    temp_sum = (features_data[0, j, i] + features_data[0, j + 1, i] + features_data[0, j + 2, i] + features_data[0, j + 3, i]) / 4
                features_data[3, j, i] = temp_sum
                if sum_LOAD > 0:
                    features_data[4, j, i] = features_data[0, j, i] / sum_LOAD

                if min_max_features_data[3, 0] > features_data[3, j, i]:
                    min_max_features_data[3, 0] = features_data[3, j, i]
                if min_max_features_data[3, 1] < features_data[3, j, i]:
                    min_max_features_data[3, 1] = features_data[3, j, i]

                if min_max_features_data[4, 0] > features_data[4, j, i]:
                    min_max_features_data[4, 0] = features_data[4, j, i]
                if min_max_features_data[4, 1] < features_data[4, j, i]:
                    min_max_features_data[4, 1] = features_data[4, j, i]

            for j in range(min(self.day_points, len(base_data.index))):
                if j > 3:
                    features_data[5, j, i] = features_data[3, j, i] - features_data[3, j - 4, i]
                else:
                    features_data[5, j, i] = features_data[3, j, i] - features_data[3, self.day_points - 1, i - 1]

                if min_max_features_data[5, 0] > features_data[5, j, i]:
                    min_max_features_data[5, 0] = features_data[5, j, i]
                if min_max_features_data[5, 1] < features_data[5, j, i]:
                    min_max_features_data[5, 1] = features_data[5, j, i]

            for j in range(min(self.day_points, len(base_data.index))):
                if features_data[0, j, i] > (sum_LOAD * 0.2):
                    features_data[6, j, i] = 1
                else:
                    features_data[6, j, i] = 0

                if min_max_features_data[6, 0] > features_data[6, j, i]:
                    min_max_features_data[6, 0] = features_data[6, j, i]
                if min_max_features_data[6, 1] < features_data[6, j, i]:
                    min_max_features_data[6, 1] = features_data[6, j, i]

            for j in range(min(self.day_points, len(base_data.index))):
                if features_data[0, j, i] > (sum_LOAD * 1.5):
                    features_data[7, j, i] = 1
                else:
                    features_data[7, j, i] = 0

                if min_max_features_data[7, 0] > features_data[7, j, i]:
                    min_max_features_data[7, 0] = features_data[7, j, i]
                if min_max_features_data[7, 1] < features_data[7, j, i]:
                    min_max_features_data[7, 1] = features_data[7, j, i]

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

                    if min_max_features_data[self.features_indexes[item]-1, 0] > features_data[self.features_indexes[item]-1, j, i]:
                        min_max_features_data[self.features_indexes[item]-1, 0] = features_data[self.features_indexes[item]-1, j, i]
                    if min_max_features_data[self.features_indexes[item]-1, 1] < features_data[self.features_indexes[item]-1, j, i]:
                        min_max_features_data[self.features_indexes[item]-1, 1] = features_data[self.features_indexes[item]-1, j, i]
        return features_data, min_max_features_data, data_target


    def _feature_norm(self, feature_data: np.ndarray, min_max_arr: np.ndarray, day, hour) -> List:
        normed_features = []
        min_max_index = 0
        for i in range(feature_data.shape[0]):
            if i < 8:
                if i != 2:
                    normed_features.append(DayFeaturesNN._normalize(feature_data[i,hour,day-1], min_max_arr[min_max_index,0],min_max_arr[min_max_index,1]))
                    normed_features.append(DayFeaturesNN._normalize(feature_data[i, hour, day - 7], min_max_arr[min_max_index, 0],min_max_arr[min_max_index, 1]))
                    min_max_index += 1
                else:
                    normed_features.append(DayFeaturesNN._normalize(feature_data[i, hour, day], min_max_arr[min_max_index, 0], min_max_arr[min_max_index, 1]))
                    min_max_index += 1
            else:
                normed_features.append(
                    DayFeaturesNN._normalize(feature_data[i, hour, day-1], min_max_arr[min_max_index, 0],min_max_arr[min_max_index, 1]))
        return normed_features


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

        self.num_par += len(self.common_features_names)
        features_data, min_max_features_data, data_target = self._features_generation()

        NN_model = Sequential()
        NN_model.add(Dense(self.num_par, kernel_initializer='normal', input_dim=self.num_par, activation='elu'))
        NN_model.add(Dense(4, kernel_initializer='normal', activation='elu'))
        NN_model.add(Dense(1, kernel_initializer='normal', activation='linear'))
        NN_model.compile(loss='mean_squared_error', optimizer='adam', metrics=['mean_squared_error'])
        NN_model.summary()

        y_before = np.zeros((self.day_points*len(self.day_list),self.num_par))

        for m in range(self.circles_count):
            print(f'Running {m+1} of {self.circles_count} data calculation cycles')
            for _ in tqdm(range(0, len(self.day_list))):
                day = self.day
                if day > 7:
                    for t in range(day_points):
                        y_before[day*self.day_points+t,:] = self._feature_norm(features_data, min_max_features_data, day, t)

                if day >= 7:
                    NN_model.fit(y_before[7*self.day_points-1:(day+1)*self.day_points-1,:], data_target[7*self.day_points-1:(day+1)*self.day_points-1],
                                 epochs=5,
                                 batch_size=len(data_target[7*self.day_points-1:(day+1)*self.day_points-1]),
                                 verbose=0)

                self.day += 1
                self.NN_model = NN_model

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
            features_data, min_max_features_data, data_target = self._features_generation(is_predicting=True)
            y_before = np.zeros((self.day_points*len(self.day_list),self.num_par))
            y_estimate = np.zeros((self.day_points, self.circles_count * len(self.day_list)))
            NN_model = self.NN_model

            self.df['forecast'] = 0
            for _ in range(self.circles_count):
                for s in range(0, len(self.day_list)):
                    day = self.day
                    if day > 7:
                        for t in range(self.day_points):
                            y_before[day * self.day_points + t, :] = self._feature_norm(features_data,min_max_features_data, day, t)

                    if day >= 8:
                        y_predict = NN_model.predict(
                            y_before[day * self.day_points - 1:(day + 1) * self.day_points - 1, :], verbose=0)

                        for t in range(self.day_points):
                            y_estimate[t, day] = y_predict[t, 0]

                            if y_estimate[t, day] > 1.5 * np.max(features_data[0, t, day - 1]):
                                y_estimate[t, day] = 1.5 * np.max(features_data[0, t, day - 1])
                            else:
                                if y_estimate[t, day] < 0:
                                    y_estimate[t, day] = 0
                    self.day += 1
            for i in range(len(self.day_list)):
                copy_to_data = self.df[self.df['date'].isin([list(self.day_list)[i]])].copy()[['date', 'time', self.value_column_name]]
                for j in range(len(copy_to_data)):
                    l = copy_to_data.index[j]
                    self.df.loc[l, 'forecast'] = float(y_estimate[j, i + (self.circles_count-1) * len(self.day_list)])
            return np.array(self.df['forecast'])
        if method == "Last":
            self._validate_dataframe(df, self.datetime_column_name, self.value_column_name)
            self._make_day_list(self.datetime_column_name)
            self.day_list = self.day_list[-7:]
            features_data, min_max_features_data, data_target = self._features_generation(is_predicting=True)
            y_before = np.zeros((self.day_points, self.num_par))


            for s in range(0, len(self.day_list)):
                for t in range(self.day_points):
                    day = len(self.day_list)
                    if day >= 7:
                        last_day = self.day_list[-1]
                        next_day = last_day + pd.Timedelta(days=1)
                        features_data[2, t, day] = 1 if next_day.weekday() in [5, 6] else 0
                        y_before[t, :] = self._feature_norm(features_data,min_max_features_data, day, t)

            y_before = np.nan_to_num(y_before, nan=0)
            y_predict = self.NN_model.predict(y_before, verbose=0)
            y_predict = y_predict.flatten()
            y_predict[y_predict < 0] = 0
            return y_predict
        else:
            raise ValueError("Incorrect size of input dataframe.")
