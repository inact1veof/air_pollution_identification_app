"""
DSM library data structure class using pd.DataFrame engine
"""
from datetime import datetime
from typing import Union, Dict, List
import numpy as np
import pandas as pd


class dsm_timeseries:
    """
    DSM timeseries class contains dataframe info

    :param name: name of dataset (str)
    :param data: dataframe with float (np.ndarray) or float+time values (pd.DataFrame)
    :param value_column_name: name of column with float values (str)
    :param interval: parameter for time interval of datetime values (if None interval can be calculated) (str)
    :param time_column_name: name of column with datetime values (if None column will be named "Time") (str)
    :param value_column_index: required parameter if data is np.ndarray, pointer to index of target column (int)
    :param datetime_arr: required parameter if data is np.ndarray, list with datetime values (list)
    :param time_format: datetime column format if it reads as str (str)
    """
    def __init__(self, name: str,
                 data: Union[pd.DataFrame, np.ndarray],
                 value_column_name: str,
                 interval: str = None,
                 time_column_name: str = None,
                 value_column_index: int = None,
                 datetime_arr: list = None,
                 time_format: str = None) -> None:
        self._time_format = time_format
        validation = self._validate_dataframe(data, time_column_name, value_column_name, datetime_arr)
        if validation:
            self.name = name
            self._time_column_name = time_column_name
            if isinstance(data, np.ndarray):
                if value_column_index is None:
                    raise ValueError(f"Enter a value column index of input numpy array. Using value_column_index=(int)")
                if datetime_arr is None:
                    raise ValueError(f"Array of datetime values is None")
                if value_column_name is None:
                    raise ValueError(f"Enter a name of value column. Using value_column_name=(str)")
                data = self._make_dataframe(data, datetime_arr, value_column_index, value_column_name, time_column_name)
            self._data = data
            df = self._data
            try:
                df[self._time_column_name] = pd.to_datetime(df[self._time_column_name])
                self._data = df
                self._make_rounded_time_values()
            except:
                raise ValueError(f"Error in converting datetime column to datetime objects")
            if interval is None:
                interval = self._calculate_interval()
            self._interval = interval
            self._value_column_name = value_column_name
        else:
            raise ValueError(f"Validation failed. Incorrect input.")

        self.show()

    def _validate_dataframe(self, data: Union[pd.DataFrame, np.ndarray], datetime_column_name: str,
                            value_column_name: str, time_arr: list = None, value_column_index: int = None) -> bool:
        """
        Method for check input data correctness

        :param data: dataframe with float (np.ndarray) or float+time values (pd.DataFrame)
        :param datetime_column_name: required parameter if data is pd.DateTime, checks for the presence of a column (str)
        :param value_column_name: required parameter if data is pd.DateTime, checks for the presence of a column (str)
        :param value_column_index: required parameter if data is np.ndarray, pointer to index of target column (int)
        :param time_arr: required parameter if data is np.ndarray, list with datetime values (list)
        :return bool flag about data correctness (True = good / Error = bad)
        """

        if isinstance(data, pd.DataFrame):
            if self._time_format is not None:
                data[datetime_column_name] = pd.to_datetime(data[datetime_column_name], format=self._time_format)
            else:
                try:
                    data[datetime_column_name] = pd.to_datetime(data[datetime_column_name])
                except:
                    raise ValueError("Incorrect type of datetime column. Must be datetime.")
            if datetime_column_name not in data.columns:
                raise ValueError(f"{datetime_column_name} not in dataframe.")
            elif value_column_name not in data.columns:
                raise ValueError(f"{value_column_name} not in dataframe.")
            if not pd.api.types.is_datetime64_any_dtype(data[datetime_column_name]):
                raise ValueError("Incorrect type of datetime column. Must be datetime.")
            elif not data[value_column_name].dtype == float:
                raise ValueError("Incorrect type of value column. Must be float.")
        if isinstance(data, np.ndarray):
            all_are_datetime = all(isinstance(item, datetime) for item in time_arr)
            if not all_are_datetime:
                raise ValueError("Incorrect type of all datetime array elements. Must be datetime.")
            if data.ndim != 1:
                if data.shape[1] >= value_column_index:
                    raise ValueError("Incorrect value column index. Must be < count of columns")
        return True

    def _format_time(self, hours: int, minutes: int) -> str:
        """
        Method for make time interval str

        :param hours: number of hours in interval between two dates (int)
        :param minutes: number of minutes in interval between two dates (int)
        :return formatted time (str)
        """
        total_minutes = hours * 60 + minutes

        if 0 < total_minutes < 1440:
            if hours > 0 and minutes > 0:
                return f"{hours}h{minutes}m"
            elif hours == 0:
                return f"{minutes}m"
            elif minutes == 0:
                return f"{hours}h"
        else:
            raise ValueError("Cannot calculating time interval between time values")

    def _make_rounded_time_values(self) -> None:
        """
        Method for round seconds in dataframe dates
        """
        df = self._data
        df[self._time_column_name] = df[self._time_column_name].apply(lambda x: x.replace(second=0))
        self._data = df

    def _calculate_interval(self) -> str:
        """
        Method for calculating Timestamp between two dates in dataframe
        """
        df = self._data
        first_value = df.iloc[0][self._time_column_name]
        second_value = df.iloc[1][self._time_column_name]

        time_diff = second_value - first_value
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60

        return self._format_time(hours, minutes)

    def _make_dataframe(self, data: np.ndarray, time_column: list, value_column_index: int,
                        value_column_name: str, time_column_name: str = None) -> pd.DataFrame:
        """
        Method for make pd.DataFrame from np.ndarray

        :param data: array with target float values and float features (np.ndarray)
        :param time_column: list with time values of dataframe (list)
        :param value_column_index: index of data column with target values (int)
        :param value_column_name: name for target column in future dataframe (str)
        :param time_column_name: name for datetime column in future dataframe (str)
        :return pd.DataFrame with float, features and datetime columns (pd.DataFrame)
        """
        if data.shape[0] != len(time_column):
            raise ValueError("Length of value and time dataframes is not same")
        else:
            df = pd.DataFrame(data)
            if time_column_name is not None:
                self._time_column_name = time_column_name
                df[time_column_name] = time_column
                target_columns = [time_column_name, value_column_name]
            else:
                self._time_column_name = 'Time'
                df['Time'] = time_column
                target_columns = ['Time', value_column_name]
            df.rename(columns={value_column_index: value_column_name}, inplace=True)

            new_order = target_columns + [col for col in df.columns if col not in target_columns]
            df = df[new_order]
            return df

    def show(self) -> None:
        """
        Method for print dsm timeseries structure info
        """
        print(f'DSM dataframe: {self.name}')
        print(f'Time interval: {self._interval}')
        print(f'Data Shape: {self._data.shape}')
        print(self._data)

    def rename_columns(self, columns: Dict[str, str]) -> None:
        """
        Method for rename dsm structure columns
        """
        self._data.rename(columns=columns, inplace=True)
        indices = list(columns.keys())
        for item in indices:
            if item == self._time_column_name:
                self._time_column_name = columns[item]
            if item == self._value_column_name:
                self._value_column_name = columns[item]

    def rename(self, new_name: str) -> None:
        """
        Method for rename dsm structure
        """
        self.name = new_name

    def drop(self, columns: List) -> None:
        """
        Method for drop some columns in dsm structure
        """
        self.data.drop(columns=columns, inplace=True)

    @property
    def data(self):
        return self._data

    @property
    def value_column_name(self):
        return self._value_column_name

    @property
    def time_column_name(self):
        return self._time_column_name
