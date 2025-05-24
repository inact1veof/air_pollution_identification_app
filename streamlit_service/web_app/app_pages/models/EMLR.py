"""
Air pollution forecasting class using base model Ensemble by linear regression
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
from .STA import STA
from .SDaysAVR import SDaysAVR
from .TDaysAVR import TDaysAVR
from .HW import HW
from .SARIMA import SARIMA
from .DayFeaturesLR import DayFeaturesLR
from .DayFeaturesNN import DayFeaturesNN



class EMLR:
    """
    Ensemble Linear Regressor Class

    :param base_models: objects of base forecasting models in DSM
    :param pretrained: indicates whether the base models are trained
    :param circles_count: number of circles of the data calculations
    :param start_day: day number for start predict
    :param *args: rls filter parameters
    :param *kwargs: rls filter parameters
    """
    def __init__(self, base_models: List, pretrained: bool = False, circles_count: int = 1, start_day: int = 7, *args, **kwargs):
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
        self.w = None
        self.args = args
        self.kwargs = kwargs
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

        self.datetime_column_name = datetime_column_name
        self.value_column_name = value_column_name
        if common_features_names is None:
            common_features_names = []
        # Validate Dataframe
        self._validate_dataframe(df, datetime_column_name, value_column_name)
        self.day_points = day_points

        model_column_names = []
        model_column_names.append(value_column_name)
        if not self.pretrained:
            for model in self.base_models:
                if isinstance(model, SDaysAVR):
                    res = model.predict(self.df, day_points, datetime_column_name, value_column_name, 'All')
                    self.df['SDaysAVR'] = res
                    model_column_names.append('SDaysAVR')
                elif isinstance(model, TDaysAVR):
                    res = model.predict(self.df, datetime_column_name, value_column_name, day_points , 'All')
                    self.df['TDaysAVR'] = res
                    model_column_names.append('TDaysAVR')
                elif isinstance(model, STA):
                    model.fit(self.df, day_points, datetime_column_name, value_column_name, common_features_names)
                    res = model.predict('All')
                    self.df['STA'] = res
                    model_column_names.append('STA')
                elif isinstance(model, HW):
                    res = model.predict(df, self.start_day, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name)
                    self.df['HW'] = res
                    model_column_names.append('HW')
                elif isinstance(model, SARIMA):
                    model.fit(df, self.start_day, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name)
                    res = model.predict(df, self.start_day, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name)
                    self.df['SARIMA'] = res
                    model_column_names.append('SARIMA')
                elif isinstance(model, DayFeaturesLR):
                    model.fit(df, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name, common_features_names=common_features_names)
                    res = model.predict(df, self.start_day, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name, common_features_names=common_features_names)
                    self.df['DayFeaturesLR'] = res
                    model_column_names.append('DayFeaturesLR')
                elif isinstance(model, DayFeaturesNN):
                    model.fit(df, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name, common_features_names=common_features_names)
                    res = model.predict(df, self.start_day, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name, common_features_names=common_features_names)
                    self.df['DayFeaturesNN'] = res
                    model_column_names.append('DayFeaturesNN')
        else:
            for model in self.base_models:
                if isinstance(model, SDaysAVR):
                    res = model.predict(self.df, day_points, datetime_column_name, value_column_name, 'All')
                    self.df['SDaysAVR'] = res
                    model_column_names.append('SDaysAVR')
                elif isinstance(model, TDaysAVR):
                    res = model.predict(self.df, datetime_column_name, value_column_name, day_points , 'All')
                    self.df['TDaysAVR'] = res
                    model_column_names.append('TDaysAVR')
                elif isinstance(model, STA):
                    res = model.predict('All')
                    self.df['STA'] = res
                    model_column_names.append('STA')
                elif isinstance(model, HW):
                    res = model.predict(df, self.start_day, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name)
                    self.df['HW'] = res
                    model_column_names.append('HW')
                elif isinstance(model, SARIMA):
                    res = model.predict(df, self.start_day, day_points, method='All', datetime_column_name=datetime_column_name, value_column_name=value_column_name)
                    self.df['SARIMA'] = res
                    model_column_names.append('SARIMA')
                elif isinstance(model, DayFeaturesLR):
                    res = model.predict(df, method='All')
                    self.df['DayFeaturesLR'] = res
                    model_column_names.append('DayFeaturesLR')
                elif isinstance(model, DayFeaturesNN):
                    res = model.predict(df, method='All')
                    self.df['DayFeaturesNN'] = res
                    model_column_names.append('DayFeaturesNN')

        self._make_day_list(datetime_column_name)

        y_estimate = np.zeros((day_points, self.circles_count * len(self.day_list)))
        base_data = np.zeros((self.num_rls_par + 1, day_points, self.circles_count * len(self.day_list)))
        w = np.zeros((day_points, self.num_rls_par))
        w_list = np.zeros((self.circles_count * len(self.day_list) * day_points, self.num_rls_par))
        df = self.df
        for i in range(self.circles_count * len(self.day_list)):
            models_data = df[df['date'].isin([list(self.day_list)[(i)%len(self.day_list)]])].copy()[model_column_names]
            for j in range(min(day_points, len(models_data.index))):
                l = models_data.index[j]
                for model_number in range(len(model_column_names)):
                    base_data[model_number, j, i] = models_data.loc[l, model_column_names[model_number]]
        self._base_data = base_data
        rls_model = FilterRLS(self.num_rls_par, *self.args, **self.kwargs)
        self.model_column_names = model_column_names
        for m in range(self.circles_count):
            print(f'Start {m+1} of {self.circles_count} cycles of data calculation')
            for _ in tqdm(range(0, len(self.day_list))):
                y_before = np.zeros((day_points, self.num_rls_par))
                for t in range(day_points):
                    if self.day > self.start_day:
                        feature_point = []
                        for num_model in range(1, len(model_column_names)):
                            feature_point.append(base_data[num_model, t, self.day])
                        y_before[t, :] = feature_point

                    y_estimate[t, self.day] = np.dot(w[t], y_before[t, :].T)

                    if y_estimate[t, self.day] > 1.5 * np.max(base_data[0, t, self.day - 1]):
                        y_estimate[t, self.day] = 1.5 * np.max(base_data[0, t, self.day - 1])
                    else:
                        if y_estimate[t, self.day] < 0:
                            y_estimate[t, self.day] = 0

                    w_list[self.day_points * self.day + t] = w[t]

                y, e, w = rls_model.run(base_data[0, :, self.day], y_before)
                self.day += 1
                self.w = w
        self.__y_estimate = y_estimate


    def _base_model_predict(self, df: pd.DataFrame, method: str = 'All') -> np.ndarray:
        if method == 'All':
            result_base_models_prediction = np.zeros((self.day_points * len(self.day_list), len(self.base_models)))
        else:
            result_base_models_prediction = np.zeros((self.day_points, len(self.base_models)))
        model_index = 0
        for model in self.base_models:
            if isinstance(model, SDaysAVR):
                res = model.predict(df, self.day_points, self.datetime_column_name, self.value_column_name, method)
                res_to_add = np.zeros(result_base_models_prediction.shape[0])
                res_to_add[res_to_add.shape[0] - res.shape[0]:] = res
                result_base_models_prediction[:, model_index] = res_to_add
            elif isinstance(model, TDaysAVR):
                res = model.predict(df, self.datetime_column_name, self.value_column_name, self.day_points, method)
                res_to_add = np.zeros(result_base_models_prediction.shape[0])
                res_to_add[res_to_add.shape[0] - res.shape[0]:] = res
                result_base_models_prediction[:, model_index] = res_to_add
            elif isinstance(model, STA):
                res = model.predict(method)
                res_to_add = np.zeros(result_base_models_prediction.shape[0])
                res_to_add[res_to_add.shape[0] - res.shape[0]:] = res
                result_base_models_prediction[:, model_index] = res_to_add
            elif isinstance(model, HW):
                res = model.predict(df, self.start_day, self.day_points, method=method,
                                    datetime_column_name=self.datetime_column_name, value_column_name=self.value_column_name)
                res_to_add = np.zeros(result_base_models_prediction.shape[0])
                res_to_add[res_to_add.shape[0] - res.shape[0]:] = res
                result_base_models_prediction[:, model_index] = res_to_add
            elif isinstance(model, SARIMA):
                res = model.predict(df, self.start_day, self.day_points, method=method,
                                    datetime_column_name=self.datetime_column_name, value_column_name=self.value_column_name)
                res_to_add = np.zeros(result_base_models_prediction.shape[0])
                res_to_add[res_to_add.shape[0] - res.shape[0]:] = res
                result_base_models_prediction[:, model_index] = res_to_add
            elif isinstance(model, DayFeaturesLR):
                res = model.predict(df, method=method)
                res_to_add = np.zeros(result_base_models_prediction.shape[0])
                res_to_add[res_to_add.shape[0] - res.shape[0]:] = res
                result_base_models_prediction[:, model_index] = res_to_add
            elif isinstance(model, DayFeaturesNN):
                res = model.predict(df, method='All')
                res = res[-72:]
                res_to_add = np.zeros(result_base_models_prediction.shape[0])
                res_to_add[res_to_add.shape[0] - res.shape[0]:] = res
                result_base_models_prediction[:, model_index] = res_to_add
            model_index += 1

        return result_base_models_prediction



    def predict(self, X: Union[pd.DataFrame, dsm_timeseries], method: str = "All") -> np.ndarray:
        """
        Method for make predict

        :param X: array of features for making regression (pd.DataFrame) one week or DSM structure
        :param method: method of forecasting (Only 1 last day = "Last", for full dataframe = "All") (str)
        :return: array of forecasts (np.array)
        """
        if method == "All":
            if isinstance(X, dsm_timeseries):
                df = X.data
            else:
                df = X
            base_model_result = self._base_model_predict(df, 'All')
            self.day = 0
            y_estimate = np.zeros((self.day_points, len(self.day_list)))
            for _ in tqdm(range(0, len(self.day_list))):
                y_before = np.zeros((self.day_points, self.num_rls_par))
                for t in range(self.day_points):
                    y_before[t,:] = base_model_result[self.day*self.day_points + t,:]

                    y_estimate[t, self.day] = np.dot(self.w[t], y_before[t, :].T)

                    if y_estimate[t, self.day] > 1.5 * np.max(self._base_data[0, t, self.day - 1]):
                        y_estimate[t, self.day] = 1.5 * np.max(self._base_data[0, t, self.day - 1])
                    else:
                        if y_estimate[t, self.day] < 0:
                            y_estimate[t, self.day] = 0
                self.day += 1
            self.df['forecast'] = 0
            for i in range(len(self.day_list)):
                copy_to_data = df[df['date'].isin([list(self.day_list)[i]])].copy()[['date', 'time', self.value_column_name]]
                for j in range(len(copy_to_data)):
                    l = copy_to_data.index[j]
                    df.loc[l, 'forecast'] = float(y_estimate[j, i])
            return np.array(df['forecast'])

        elif method == 'Last':
            if isinstance(X, dsm_timeseries):
                df = X.data
            else:
                df = X
            base_model_result = self._base_model_predict(df, 'Last')
            result = []
            for i in range(base_model_result.shape[0]):
                res = np.dot(self.w[i], base_model_result[i, :].T)
                if res > 1.5 * np.max(self._base_data[0, i, len(self.day_list)-1]):
                    result.append(1.5 * np.max(self._base_data[0, i, len(self.day_list)-1]))
                elif res < 0:
                    result.append(0)
                else:
                    result.append(res)

            return np.array(result)

