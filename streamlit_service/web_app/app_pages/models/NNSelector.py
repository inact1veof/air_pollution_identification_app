"""
Air pollution forecasting class using model selection by neural network
"""
import warnings
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tensorflow.python.keras.regularizers import l2
from tqdm import tqdm
from typing import Union, List, Dict, Any
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.optimizers import SGD
from .dsm_timeseries import dsm_timeseries
from .BaseModel import BaseModel
from .STA import STA
from .SDaysAVR import SDaysAVR
from .TDaysAVR import TDaysAVR
from .HW import HW
from .DayFeaturesLR import DayFeaturesLR
from .DayFeaturesNN import DayFeaturesNN
from .SARIMA import SARIMA
from .metrics import rmse


class NNSelector():
    """
    Neural network Selector Class

    :param base_models: objects of base forecasting models in DSM (list)
    :param pretrained: indicates whether the base models are trained (bool)
    :param circles_count: number of circles of the data calculations (int)
    :param start_day: day number for start predict (int)
    :param *args: keras neural network parameters
    :param *kwargs: count of keras neural network parameters
    """
    def __init__(self, base_models: List, pretrained: bool = False, circles_count: int = 1, start_day: int = 5, *args, **kwargs):
        res = self._validate_models(base_models)
        if res:
            self.base_models = base_models
            self.num_rls_par = len(base_models)
        else:
            raise ValueError(f"Base models must be from DSM.models")
        self.circles_count = circles_count
        self.pretrained = pretrained
        self.start_day = start_day
        self.day = 0
        self.days_number = 0
        self.df = None
        self.day_list = None
        self.day_points = 0
        self._features_number = 8
        self.ndays = 14
        self.w = None
        self.datetime_column_name = None
        self.value_column_name = None
        self.common_features_names = None
        self.model_column_names = None
        self.__y_estimate = None

    def _validate_models(self, base_models: List) -> bool:
        return all(isinstance(obj, BaseModel) for obj in base_models)

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

    def fit(self, df: Union[pd.DataFrame, dsm_timeseries], start_day: int, day_points: int, datetime_column_name: str = None,
            value_column_name: str = None, common_features_names: List[str] = None) -> None:
        """
        Fit method for model choosing

        :param df: pandas dataframe with datetime and value columns or DSM structure (pd.DataFrame, dsm_timeseries)
        :param start_day: day of starting forecast (int)
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
        self.day_points = day_points
        self.datetime_column_name = datetime_column_name
        self.value_column_name = value_column_name
        if common_features_names is None:
            common_features_names = []
        # Validate Dataframe
        self._validate_dataframe(df, datetime_column_name, value_column_name)

        model_column_names = []
        models_rmse_column_names = []
        model_column_names.append(value_column_name)
        if not self.pretrained:
            for model in self.base_models:
                if isinstance(model, SDaysAVR):
                    res = model.predict(self.df, day_points, datetime_column_name, value_column_name, 'All')
                    self.df['SDaysAVR'] = res
                    model_column_names.append('SDaysAVR')
                    model_rmse = rmse(self.df, value_column_name, 'SDaysAVR', datetime_column_name)
                    self.df['SDaysAVR_RMSE'] = model_rmse
                    models_rmse_column_names.append('SDaysAVR_RMSE')

                elif isinstance(model, TDaysAVR):
                    res = model.predict(self.df, datetime_column_name, value_column_name, day_points, 'All')
                    self.df['TDaysAVR'] = res
                    model_column_names.append('TDaysAVR')
                    model_rmse = rmse(self.df, value_column_name, 'TDaysAVR', datetime_column_name)
                    self.df['TDaysAVR_RMSE'] = model_rmse
                    models_rmse_column_names.append('TDaysAVR_RMSE')
                elif isinstance(model, STA):
                    model.fit(self.df, day_points, datetime_column_name, value_column_name, common_features_names)
                    res = model.predict('All')
                    self.df['STA'] = res
                    model_column_names.append('STA')
                    model_rmse = rmse(self.df, value_column_name, 'STA', datetime_column_name)
                    self.df['STA_RMSE'] = model_rmse
                    models_rmse_column_names.append('STA_RMSE')
                elif isinstance(model, DayFeaturesLR):
                    model.fit(self.df, day_points, datetime_column_name, value_column_name, common_features_names)
                    res = model.predict(self.df, 'All')
                    self.df['DayFeaturesLR'] = res
                    model_column_names.append('DayFeaturesLR')
                    model_rmse = rmse(self.df, value_column_name, 'DayFeaturesLR', datetime_column_name)
                    self.df['DayFeaturesLR_RMSE'] = model_rmse
                    models_rmse_column_names.append('DayFeaturesLR_RMSE')
                elif isinstance(model, HW):
                    res = model.predict(df, 14, day_points, method='All', datetime_column_name=datetime_column_name,
                                        value_column_name=value_column_name)
                    self.df['HW'] = res
                    model_column_names.append('HW')
                    model_rmse = rmse(self.df, value_column_name, 'HW', datetime_column_name)
                    self.df['HW_RMSE'] = model_rmse
                    models_rmse_column_names.append('HW_RMSE')
                if isinstance(model, SARIMA):
                    model.fit(df, 24, day_points)
                    res = model.predict(method='All')
                    self.df['SARIMA'] = res
                    model_column_names.append('SARIMA')
                    model_rmse = rmse(self.df, value_column_name, 'SDaysAVR', datetime_column_name)
                    self.df['SARIMA_RMSE'] = model_rmse
                    models_rmse_column_names.append('SARIMA_RMSE')
                if isinstance(model, DayFeaturesNN):
                    model.fit(self.df, day_points, datetime_column_name, value_column_name, common_features_names)
                    res = model.predict(self.df, 'All')
                    self.df['DayFeaturesNN'] = res
                    model_column_names.append('DayFeaturesNN')
                    model_rmse = rmse(self.df, value_column_name, 'DayFeaturesNN', datetime_column_name)
                    self.df['DayFeaturesNN_RMSE'] = model_rmse
                    models_rmse_column_names.append('DayFeaturesNN_RMSE')
        else:
            for model in self.base_models:
                if isinstance(model, SDaysAVR):
                    res = model.predict(self.df, day_points, datetime_column_name, value_column_name, 'All')
                    self.df['SDaysAVR'] = res
                    model_column_names.append('SDaysAVR')
                    model_rmse = rmse(self.df, value_column_name, 'SDaysAVR', datetime_column_name)
                    self.df['SDaysAVR_RMSE'] = model_rmse
                    models_rmse_column_names.append('SDaysAVR_RMSE')

                elif isinstance(model, TDaysAVR):
                    res = model.predict(self.df, datetime_column_name, value_column_name, day_points, 'All')
                    self.df['TDaysAVR'] = res
                    model_column_names.append('TDaysAVR')
                    model_rmse = rmse(self.df, value_column_name, 'TDaysAVR', datetime_column_name)
                    self.df['TDaysAVR_RMSE'] = model_rmse
                    models_rmse_column_names.append('TDaysAVR_RMSE')
                elif isinstance(model, STA):
                    res = model.predict('All')
                    self.df['STA'] = res
                    model_column_names.append('STA')
                    model_rmse = rmse(self.df, value_column_name, 'STA', datetime_column_name)
                    self.df['STA_RMSE'] = model_rmse
                    models_rmse_column_names.append('STA_RMSE')
                elif isinstance(model, DayFeaturesLR):
                    res = model.predict(self.df, 'All')
                    self.df['DayFeaturesLR'] = res
                    model_column_names.append('DayFeaturesLR')
                    model_rmse = rmse(self.df, value_column_name, 'DayFeaturesLR', datetime_column_name)
                    self.df['DayFeaturesLR_RMSE'] = model_rmse
                    models_rmse_column_names.append('DayFeaturesLR_RMSE')
                elif isinstance(model, HW):
                    res = model.predict(df, 14, day_points, method='All', datetime_column_name=datetime_column_name,
                                        value_column_name=value_column_name)
                    self.df['HW'] = res
                    model_column_names.append('HW')
                    model_rmse = rmse(self.df, value_column_name, 'HW', datetime_column_name)
                    self.df['HW_RMSE'] = model_rmse
                    models_rmse_column_names.append('HW_RMSE')
                if isinstance(model, SARIMA):
                    res = model.predict(method='All')
                    self.df['SARIMA'] = res
                    model_column_names.append('SARIMA')
                    model_rmse = rmse(self.df, value_column_name, 'SDaysAVR', datetime_column_name)
                    self.df['SARIMA_RMSE'] = model_rmse
                    models_rmse_column_names.append('SARIMA_RMSE')
                if isinstance(model, DayFeaturesNN):
                    res = model.predict(self.df, 'All')
                    self.df['DayFeaturesNN'] = res
                    model_column_names.append('DayFeaturesNN')
                    model_rmse = rmse(self.df, value_column_name, 'DayFeaturesNN', datetime_column_name)
                    self.df['DayFeaturesNN_RMSE'] = model_rmse
                    models_rmse_column_names.append('DayFeaturesNN_RMSE')

        self._make_day_list(datetime_column_name)

        y_estimate = np.zeros((day_points, self.circles_count * len(self.day_list)))
        MODEL_number = np.zeros((day_points, self.circles_count * len(self.day_list)))
        LOAD_data = np.zeros((self.num_rls_par + 1, day_points, self.circles_count * len(self.day_list)))
        RMSE_data = np.zeros((2, self.circles_count * len(self.day_list), self.num_rls_par))
        for i in range(self.circles_count * len(self.day_list)):
            query_names = []
            query_names.extend(model_column_names)
            query_names.extend(models_rmse_column_names)
            copy_from_data = df[df['date'].isin([list(self.day_list)[(i) % len(self.day_list)]])].copy()[query_names]
            for j in range(0, len(copy_from_data.index)):
                if j >= self.day_points:
                    continue
                rmse_data = []
                l = copy_from_data.index[j]
                model_names = model_column_names[1:]
                for model_index in range(0, self.num_rls_par):
                    LOAD_data[model_index, j, i] = copy_from_data.loc[l, model_names[model_index]]
                    rmse_values = copy_from_data.loc[l, models_rmse_column_names[model_index]]
                    rmse_data.append(rmse_values)
            RMSE_data[0, i, :] = rmse_data
            index_min_RMSE = np.where(RMSE_data[0, i, :] == np.amin(RMSE_data[0, i, :]))
            RMSE_data[1, i, index_min_RMSE[0][0]] = 1

        NN_model = Sequential()
        NN_model.add(Dense(64, activation='relu', input_dim=self.num_rls_par))
        NN_model.add(Dense(32, activation='relu'))
        NN_model.add(Dense(16, activation='relu'))
        NN_model.add(Dropout(0.1))
        NN_model.add(Dense(self.num_rls_par, activation='softmax'))

        sgd = SGD(learning_rate=0.001, weight_decay=1e-6, momentum=0.9, nesterov=True)
        NN_model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

        for m in range(self.circles_count):
            for s in range(0, len(self.day_list)):
                if self.day > start_day:
                    model_indexes = NN_model.predict(RMSE_data[0, self.day - 1:self.day, :], verbose=0)
                    print(model_indexes)
                    model_index = np.where(model_indexes[0, :] == np.amax(model_indexes[0, :]))

                    for t in range(self.day_points):
                        y_estimate[t, self.day] = LOAD_data[model_index[0][0], t, self.day]
                        MODEL_number[t, self.day] = model_index[0][0]

                if (self.day >= start_day) and (self.day < len(self.day_list)):
                    NN_model.fit(RMSE_data[0, start_day - 1:self.day, :], RMSE_data[1, start_day:self.day + 1, :], epochs=5,
                                 batch_size=len(RMSE_data[0, start_day - 1:self.day, :]), verbose=0)

                self.day = self.day + 1
        self.__y_estimate = y_estimate

    def predict(self, X: Union[pd.DataFrame, dsm_timeseries], method: str = "All") -> np.ndarray:
        """
        Method for make predict

        :param X: array of features for making regression (pd.DataFrame) one week or DSM structure
        :param method: method of forecasting (Only 1 last day = "Last", for full dataframe = "All") (str)
        :return: array of forecasts (np.array)
        """
        if method == "All":
            self.day = 0
            forecast = []

            y_estimate = self.__y_estimate
            for i in range(len(self.day_list)):
                copy_to_data = self.df[self.df['date'].isin([list(self.day_list)[i]])].copy()[
                    ['date', 'time', self.value_column_name]]
                for j in range(min(len(copy_to_data), self.day_points)):
                    l = copy_to_data.index[j]
                    forecast.append(float(y_estimate[j, i + (self.circles_count - 1) * len(self.day_list)]))
            return np.array(forecast)