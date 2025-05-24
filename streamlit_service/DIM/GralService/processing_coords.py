import json

import geopandas
import pandas as pd
import pyproj
from typing import cast, Final, Tuple

import shapely
from matplotlib import pyplot as plt
from shapely import Point, get_coordinates
from datetime import datetime
from shapely.ops import unary_union

MSK_50_2_CRS: Final[
    str] = '+proj=tmerc +lat_0=0 +lon_0=38.48333333333 +k=1 +x_0=2250000 +y_0=-5712900.566 +ellps=krass +towgs84=23.57,-140.95,-79.8,0,0.35,0.79,-0.22 +units=m +no_defs'

MSK_48_CRS: Final[
    str] = '+proj=tmerc +lat_0=0 +lon_0=38.48333333333 +k=1 +x_0=1250000 +y_0=-5412900.566 +ellps=krass +towgs84=23.57,-140.95,-79.8,0,0.35,0.79,-0.22 +units=m +no_defs'

MSK_47_CRS: Final[
    str] = "+proj=tmerc +lat_0=0 +lon_0=27.95 +k=1 +x_0=1250000 +y_0=-6211057.628 +ellps=krass +towgs84=23.57,-140.95,-79.8,0,0.35,0.79,-0.22 +units=m +no_defs"

MSK_74_CRS_TEST: Final[
    str] = "+proj=tmerc +lat_0=0 +lon_0=64.03333333333 +k=1 +x_0=3300000 +y_0=-5509414.70 +ellps=krass +towgs84=23.57,-140.95,-79.8,0,0.35,0.79,-0.22 +units=m +no_defs"


def wgs84_point_to_crs(point: tuple[float, float], crs: str) -> tuple[float, float]:
    """
    Проецирует точку из WGS84 в указанную CRS

    @param point: Точка с координатами X и Y
    @param crs: Целевая система координат (crs)
    @return: Точка с координатами, спроецированными в указанную систему
    """
    return cast(tuple[float, float],
                pyproj.Transformer.from_crs('EPSG:4326', crs, always_xy=True, ).transform(*point, errcheck=True))


def crs_point_to_wgs84(point: tuple[float, float], crs: str) -> tuple[float, float]:
    """
    Проецирует точку из указанной CRS в WGS84

    @param point: Точка с координатами X и Y
    @param crs: Текущая система координат (crs)
    @return: Точка с координатами, спроецированными в WGS84
    """
    return cast(tuple[float, float],
                pyproj.Transformer.from_crs(crs, 'EPSG:4326', always_xy=True, ).transform(*point, errcheck=True))


def read_grid_to_geodataframe(path: str,
                              target_crs: str,
                              left_bottom: tuple[float, float] | None = None) -> tuple[geopandas.GeoDataFrame, dict]:
    """
    Считывание подготовленного файла с сеткой и полями данных, перевод в GeoDataFrame со столбцами [value, coordinates]:
        value - Значение в точке сетки
        coordinates - shapely.Point с координатами X, Y в указанной системе координат (target_crs) относительно левого
    нижнего угла сетки файла
    Расстояние между точками рассчитывается с помощью шага cellsize из файла

    Parameters
    ----------
    path - Путь к файлу сетки
    target_crs - Координаты точек переводятся из WGS84 в указанную систему координат
    left_bottom - Координаты левого нижнего угла сетки в системе WGS84


    Returns
    -------
    GeoDataFrame с координатами точек сетки и их значениями, словарь с метаданными файла сетки
    """
    with open(path, 'r', encoding='utf-8') as file:
        ncols = int(file.readline().split(" ")[-1])
        nrows = int(file.readline().split(" ")[-1])

        # Координаты X, Y левого нижнего угла в рамках сетки модели
        # Нужны для получения координат источников выбросов
        model_xllcorner = float(file.readline().split(" ")[-1])
        model_yllcorner = float(file.readline().split(" ")[-1])

        # Координаты X, Y левого нижнего угла в указанной координатной системе
        # При наличии координат, относительно них будут построены точки выходного файла границ
        xllcorner = None
        yllcorner = None
        if left_bottom is not None:
            xllcorner, yllcorner = wgs84_point_to_crs(left_bottom, target_crs)

        cellsize = int(file.readline().split(" ")[-1])

        NODATA_value = file.readline()
        unit = None

        if "Unit:" in NODATA_value:
            temp = NODATA_value.replace("\t", "").split(" ")
            while '' in temp:
                temp.remove('')
            NODATA_value = temp[1]
            unit = temp[-1][5:-1]
        else:
            NODATA_value = int(NODATA_value.split(" ")[-1])

        height_temp_list = []

        # !!! Для корректного вычисления смещения, координаты должны быть в местной системе координат,
        # где смещение на 1км = +1.0 к координате (например MSK-48)

        # Индексы строк в порядке относительно левого нижнего угла в правый верхний угол
        for row in range(nrows - 1, -1, -1):
            row_values = file.readline().split(" ")
            for column in range(ncols):
                if xllcorner is None or yllcorner is None:
                    height_temp_list.append({
                        'value': float(row_values[column]),
                        'coordinates': Point(
                            column * cellsize,
                            row * cellsize
                        )
                    })
                else:
                    height_temp_list.append({
                        'value': float(row_values[column]),
                        'coordinates': Point(
                            xllcorner + column * cellsize,
                            yllcorner + row * cellsize
                        )
                    })

        geo_df = geopandas.GeoDataFrame(height_temp_list, geometry='coordinates', crs=target_crs)

        metadata = {
            "ncols": ncols,
            "nrows": nrows,
            "model_xllcorner": model_xllcorner,
            "model_yllcorner": model_yllcorner,
            "xllcorner_crs": xllcorner,
            "yllcorner_crs": yllcorner,
            "target_crs": target_crs,
            "cellsize": cellsize,
            "NODATA_value": NODATA_value,
            "unit": unit
        }
        return geo_df, metadata


def parse_contours(data: geopandas.GeoDataFrame,
                   value_column_name: str,
                   coords_column_name: str,
                   cellsize: int | float) -> tuple[geopandas.GeoDataFrame, geopandas.GeoDataFrame]:
    """
    Выделение полигонов и контуров зон с одинаковым значением в точках, сохраняется координатная система входных данных

    Parameters
    ----------
    data - Датафрейм с обязательными столбцами координат точек (coords), значений в этих точках (value)
     и указанной CRS
    value_column_name - Имя столбца с int/float значениями в точках
    coords_column_name - Имя столбца с координатами точек в формате Point(lat, long)/Point(X, Y)
    cellsize - Размер шага сетки для генерации полигонов

    Returns
    -------
    Массив с полигонами выделенных зон и массив с соответствующими контурами выделенных зон
    со столбцами value (значение) и geometry (shapely фигуры)
    """
    geometry_list = []
    geometry_boundary_list = []

    for value, group in data.groupby(value_column_name):
        points = []
        for point in group[coords_column_name].values:
            # Каждая точка находится в центре "квадратика" сетки размера cellsize*cellsize,
            # добавляется квадратный буфер размера cellsize/2 вокруг точки для получения ее зоны
            points.append(point.buffer(cellsize / 2, cap_style="square", join_style="mitre"))

        # Объединение всех точек одного значения в полигон
        poly = unary_union(points)

        geometry_list.append({"value": value,
                              "geometry": poly})
        geometry_boundary_list.append({"value": value,
                                       "geometry": poly.boundary})

    geo_polygons_df = geopandas.GeoDataFrame(geometry_list, geometry='geometry', crs=data.crs)
    geo_polygons_boundary_df = geopandas.GeoDataFrame(geometry_boundary_list, geometry='geometry', crs=data.crs)

    return geo_polygons_df, geo_polygons_boundary_df


def get_top_right_corner(lower_left_corner: tuple[int, int],
                         cellsize: int,
                         nrows: int,
                         ncols: int) -> tuple[int, int]:
    """
    Получение координат правого верхнего угла сетки в системе координат сетки

    Parameters
    ----------
    lower_left_corner - Координаты левого нижнего угла [X, Y]
    cellsize - Размер шага сетки
    nrows - Количество строк сетки
    ncols - Количество столбцов сетки

    Returns
    -------
    Координаты правого верхнего угла [X, Y]
    """
    return lower_left_corner[0] + (ncols * cellsize), lower_left_corner[1] + (nrows * cellsize)


def read_point_pollutant_sources(path: str,
                                 grid_metadata: dict,
                                 output_coords_in_WGS84: bool = True,
                                 verbose: bool = True) -> dict | None:
    """
    Сохраняет данные о точечных источниках загрязнения в словарь для экспорта в json
    Если в метаданных присутствуют координаты левого нижнего угла в crs, то координаты источников сохраняются
    относительно указанного угла, иначе сохраняются в системе координат модели (как записаны в исходном файле)

    Формат: {"Name": {"lat": 111, "lon": 222}...}

    Parameters
    ----------
    path - Путь к файлу с данными источников
    grid_metadata - Метаданные сетки для получения координат углов и crs данных
    output_coords_in_WGS84 - Координаты источников возвращаются в WGS84 или в указанной в метаданных системе координат
    verbose - Предупреждения и сообщения об ошибках выводятся в консоль

    Returns
    -------
    Словарь с данными источников при успехе, при ошибке возвращает None
    """
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
            if len(lines) > 2:
                pollution_centres = {}

                for i in range(2, len(lines)):
                    row = lines[i].split(",")

                    name = row[0]
                    x_data = row[1]
                    y_data = row[2]

                    if (grid_metadata["xllcorner_crs"] is not None and
                            grid_metadata["yllcorner_crs"] is not None):

                        x_offset_meters = abs(grid_metadata["model_xllcorner"] - float(x_data))
                        y_offset_meters = abs(grid_metadata["model_yllcorner"] - float(y_data))

                        x = grid_metadata["xllcorner_crs"] + x_offset_meters
                        y = grid_metadata["yllcorner_crs"] + y_offset_meters

                        if output_coords_in_WGS84:
                            x, y = crs_point_to_wgs84((x, y), grid_metadata["target_crs"])

                        pollution_centres[name] = {
                            "lat": x,
                            "lon": y
                        }
                    else:
                        pollution_centres[name] = {
                            "lat": x_data,
                            "lon": y_data
                        }

                return pollution_centres
            else:
                if verbose:
                    print(f"ВНИМАНИЕ! В файле {path} нет данных о центрах выбросов.")
    except FileNotFoundError:
        if verbose:
            print(f"ВНИМАНИЕ! Файл {path} не найден.")


def read_areal_pollutant_sources(path: str,
                                 grid_metadata: dict,
                                 output_coords_in_WGS84: bool = True,
                                 verbose: bool = True) -> dict | None:
    """
    Сохраняет данные о площадных источниках загрязнения в словарь для экспорта в json
    ! Сохраняется координата только первой из четырех точек площади !
    Если в метаданных присутствуют координаты левого нижнего угла в crs, то координаты источников сохраняются
    относительно указанного угла, иначе сохраняются в системе координат модели (как записаны в исходном файле)

    Формат: {"Name": {"lat": 111, "lon": 222}...}

    Parameters
    ----------
    path - Путь к файлу с данными источников
    grid_metadata - Метаданные сетки для получения координат углов и crs данных
    output_coords_in_WGS84 - Координаты источников возвращаются в WGS84 или в указанной в метаданных системе координат
    verbose - Предупреждения и сообщения об ошибках выводятся в консоль

    Returns
    -------
    Словарь с данными источников при успехе, при ошибке возвращает None
    """
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
            if len(lines) > 2:
                pollution_centres = {}

                for i in range(2, len(lines)):
                    row = lines[i].split(",")

                    name = row[0]
                    x_data = row[27]
                    y_data = row[28]

                    if (grid_metadata["xllcorner_crs"] is not None and
                            grid_metadata["yllcorner_crs"] is not None):

                        x_offset_meters = abs(grid_metadata["model_xllcorner"] - float(x_data))
                        y_offset_meters = abs(grid_metadata["model_yllcorner"] - float(y_data))

                        x = grid_metadata["xllcorner_crs"] + x_offset_meters
                        y = grid_metadata["yllcorner_crs"] + y_offset_meters

                        if output_coords_in_WGS84:
                            x, y = crs_point_to_wgs84((x, y), grid_metadata["target_crs"])

                        pollution_centres[name] = {
                            "lat": x,
                            "lon": y
                        }
                    else:
                        pollution_centres[name] = {
                            "lat": x_data,
                            "lon": y_data
                        }

                return pollution_centres
            else:
                if verbose:
                    print(f"ВНИМАНИЕ! В файле {path} нет данных о центрах выбросов.")
    except FileNotFoundError:
        if verbose:
            print(f"ВНИМАНИЕ! Файл {path} не найден.")


def read_pollutant_name(path: str, verbose: bool = True) -> str | None:
    """
    Получает строку с названием вещества для экспорта в json

    Parameters
    ----------
    path - Путь к файлу с данными
    verbose - Предупреждения и сообщения об ошибках выводятся в консоль

    Returns
    -------
    Строка с названием вещества при успехе, при ошибке возвращает None
    """
    try:
        with open(path, 'r') as file:
            pollutant_name = file.readline().rstrip("\n")

            return pollutant_name

    except FileNotFoundError:
        if verbose:
            print(f"ВНИМАНИЕ! Файл {path} не найден.")


def read_wind_data(path: str,
                   line_number: int | None = -1,
                   verbose: bool = True) -> tuple[str | None, float | None, float | None]:
    """
    Получает метаданные о ветре и дате получения данных для экспорта в json

    Parameters
    ----------
    wind_data_path - Путь к файлу с данными
    wind_data_line_number - Номер строки в файле, которую следует использовать для получения данных, начиная с 1
     Последняя строка файла = -1
     При отсутствии будет спользована последняя строка файла
    verbose - Предупреждения и сообщения об ошибках выводятся в консоль

    Returns
    -------
    Строка даты и времени (datetime.isoformat), скорость ветра в км/ч, направление ветра в градусах при успехе, иначе None
    """
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
            if len(lines) == 0:
                if verbose:
                    print(f"ВНИМАНИЕ! Файл {path} не имеет данных для создания метаданных о ветре, "
                          f"они будут установлены как None. Текущее время будет записано в метаданные.")
                date_time = datetime.now().isoformat()

                return date_time, None, None
            else:
                if line_number > len(lines):
                    if verbose:
                        print(f"ВНИМАНИЕ! Файл {path} не имеет строки №{line_number}, она не может "
                              f"использоваться для создания метаданных о ветре. Будет использована последняя строка файла.")
                    line_number = -1

                row = lines[line_number].split(",")

                date_time = datetime.strptime(row[0] + " " + row[1], "%d.%m.%Y %H:%M").isoformat()
                wind_speed_kph = float(row[2])
                wind_dir_deg = float(row[3])

        return date_time, wind_speed_kph, wind_dir_deg

    except FileNotFoundError:
        if verbose:
            print(f"ВНИМАНИЕ! Файл {path} не найден.")

        return None, None, None


def create_metadata_from_files(pollutant_path: str | None,
                               point_pollutant_sources_path: str | None,
                               areal_pollutant_sources_path: str | None,
                               grid_metadata: dict | None,
                               wind_data_path: str | None,
                               wind_data_line_number: int | None = -1,
                               output_coords_in_WGS84: bool = True,
                               verbose: bool = True) -> dict:
    """
    Создание словаря метаданных для сохранения в json файл
    Если путь к необходимому файлу отсутствует, то значение поля в словаре будет равно None

    Parameters
    ----------
    pollutant_path - Путь к файлу с названием вещества
    point_pollutant_sources_path - Путь к файлу с точечными источниками выбросов
    areal_pollutant_sources_path - Путь к файлу с площадными источниками выбросов
    grid_metadata - Метаданные сетки модели
    wind_data_path - Путь к метео файлу с данными о ветре и дате
    wind_data_line_number - Номер строки в файле, которую следует использовать для получения данных, начиная с 1
     Последняя строка файла = -1
     При отсутствии будет спользована последняя строка файла
    output_coords_in_WGS84 - Координаты источников возвращаются в WGS84 или в указанной в метаданных системе координат
    verbose - Предупреждения и сообщения об ошибках выводятся в консоль

    Returns
    -------
    Словарь с метаданными

    """
    pollutant_name = None
    date_time = None
    wind_speed_kph = None
    wind_dir_deg = None
    point_pollution_centres = None
    areal_pollution_centres = None

    # Название вещества
    if pollutant_path is not None:
        pollutant_name = read_pollutant_name(path=pollutant_path,
                                             verbose=verbose)
    else:
        if verbose:
            print("ВНИМАНИЕ! Нет файла с данными о названии вещества.")

    # Координаты точечных источников выбросов
    if point_pollutant_sources_path is not None:
        point_pollution_centres = read_point_pollutant_sources(path=point_pollutant_sources_path,
                                                               grid_metadata=grid_metadata,
                                                               output_coords_in_WGS84=output_coords_in_WGS84,
                                                               verbose=verbose)
    else:
        if verbose:
            print("ВНИМАНИЕ! Нет файла с данными о точечных центрах выбросов.")

    # Координаты площадных источников выбросов
    if areal_pollutant_sources_path is not None:
        areal_pollution_centres = read_areal_pollutant_sources(path=areal_pollutant_sources_path,
                                                               grid_metadata=grid_metadata,
                                                               output_coords_in_WGS84=output_coords_in_WGS84,
                                                               verbose=verbose)
    else:
        if verbose:
            print("ВНИМАНИЕ! Нет файла с данными о площадных центрах выбросов.")

    # Дата, скорость и направление ветра
    if wind_data_path is not None:
        date_time, wind_speed_kph, wind_dir_deg = read_wind_data(path=wind_data_path,
                                                                 line_number=wind_data_line_number,
                                                                 verbose=verbose)
    else:
        if verbose:
            print("ВНИМАНИЕ! Нет файла с данными о ветре.")

    return {
        "metadata":
            {
                'pollutant': pollutant_name,
                'datetime': date_time,
                'wind_speed_kph': wind_speed_kph,
                'wind_dir_deg': wind_dir_deg,
                'point_pollution_centres': point_pollution_centres,
                'areal_pollution_centres': areal_pollution_centres
            }
    }


def save_data_as_json(height_data: pd.DataFrame | geopandas.GeoDataFrame,
                      pollution_data: pd.DataFrame | geopandas.GeoDataFrame,
                      metadata: dict,
                      output_file_name: str) -> dict:
    """
    Сохранение данных о фигурах карты высот и карты выбросов, словаря метаданных в json-файл
    определенного формата

    Parameters
    ----------
    height_data - Датафрейм контуров/полигонов карты высот со столбцами значений (value) и shapely геометрии (geometry)
    pollution_data - Датафрейм контуров/полигонов карты выбросов со столбцами значений (value) и shapely геометрии
     (geometry)
    metadata - Словарь с метаданными, добавляемый в конец json файла
    output_file_name - Имя сохраняемого json файла

    Returns
    -------
    Словарь с данными в определенном формате, аналогичный сохраняется как json файл по указанному в имени пути

    """
    result = {}
    geometry = {}

    for dataframe, data_type in [[height_data, "heightmap"],
                                 [pollution_data, "pollution"]]:

        geometry[data_type] = []
        if dataframe is not None and dataframe.shape[0] > 0:
            # Датафреймы должны быть с колонками значений value и фигурами-координатами geometry
            for index, row in dataframe.iterrows():
                row_dict = {
                    "type": None,
                    "value": row["value"],
                    "data": []
                }

                # Обработка MultiLineString / MultiPolygon
                if (isinstance(row["geometry"], shapely.MultiLineString) or
                        isinstance(row["geometry"], shapely.MultiPolygon)):
                    # Определение типа фигуры
                    if isinstance(row["geometry"], shapely.MultiLineString):
                        row_dict["type"] = "MultiLineString"
                    else:
                        row_dict["type"] = "MultiPolygon"

                    # Добавление координат фигуры
                    for line in row["geometry"].geoms:
                        line_list = []
                        for point in get_coordinates(line):
                            line_list.append({"lat": float(point[0]),
                                              "lon": float(point[1])})
                        row_dict["data"].append(line_list)

                # Обработка LineString и Point / Polygon
                if (isinstance(row["geometry"], shapely.LineString) or
                        isinstance(row["geometry"], shapely.Point) or
                        isinstance(row["geometry"], shapely.Polygon)):
                    # Определение типа фигуры
                    if isinstance(row["geometry"], shapely.LineString):
                        row_dict["type"] = "LineString"
                    elif isinstance(row["geometry"], shapely.Point):
                        row_dict["type"] = "Point"
                    else:
                        row_dict["type"] = "Polygon"

                    # Добавление координат фигуры
                    line_list = []
                    for point in get_coordinates(row["geometry"]):
                        line_list.append({"lat": float(point[0]),
                                          "lon": float(point[1])})
                    row_dict["data"].append(line_list)

                geometry[data_type].append(row_dict)

    # Добавление данных и метаданных
    result["geometry"] = geometry
    result["metadata"] = metadata["metadata"]

    # Сохранение полученного файла в json
    with open(output_file_name + '.json', 'w') as file:
        json.dump(result, file, indent=4)

    return result


def round_pollution_values(data: pd.DataFrame | geopandas.GeoDataFrame,
                           column_name: str,
                           agg_type: str = "interval_mean",
                           count: int = 5,
                           threshold: float = 1) -> pd.DataFrame | geopandas.GeoDataFrame:
    """
    Обработка значений выбросов:
    1. Отбрасываются значения выбросов равные нулю
    2. Все значения ниже границы (threshold, по умолчанию 1) округляются до указанного количества интервалов
    3. Все значения выше границы округляются до целого числа

    Parameters
    ----------
    data - Датафрейм с данными
    column_name - Имя столбца с обрабатываемыми данными
    count - Количество интервалов для значений ниже границы (threshold)
    agg_type - Тип округления значений в интервалах ('interval_mean', 'values_mean', 'interval_max')
    threshold - Граница разделения данных

    Returns
    -------
    Датафрейм с элементами, количество уникальных значений которых уменьшено, но общее количество сохранено
    """
    data_copy = data.copy()

    data_copy = cut_by_threshold(data=data_copy,
                                 column_name="value",
                                 threshold=0,
                                 is_lower=True,
                                 including=False)

    if data_copy.shape[0] == 0:
        return data_copy

    mask = data_copy[column_name] >= threshold

    less_than_threshold_data = data_copy[~mask]
    more_than_threshold_data = data_copy[mask]

    if less_than_threshold_data.shape[0] > 0:
        less_than_threshold_data.loc[:, column_name] = less_than_threshold_data[column_name].round(2)
        less_than_threshold_data = interval_rounding(data=less_than_threshold_data,
                                                     column_name=column_name,
                                                     count=count,
                                                     agg_type=agg_type)
        less_than_threshold_data.loc[:, column_name] = less_than_threshold_data[column_name].round(2)

    if more_than_threshold_data.shape[0] > 0:
        more_than_threshold_data.loc[:, column_name] = more_than_threshold_data[column_name].round(0)

    result = pd.concat([less_than_threshold_data, more_than_threshold_data], ignore_index=True)

    result = cut_by_threshold(data=result,
                              column_name="value",
                              threshold=0,
                              is_lower=True,
                              including=False)

    return result


def interval_rounding(data: pd.DataFrame | geopandas.GeoDataFrame,
                      column_name: str,
                      count: int = 3,
                      agg_type: str = "interval_mean") -> pd.DataFrame | geopandas.GeoDataFrame:
    """
    Округление значений с помощью разделения на интервалы, значения всех элементов внутри интервала приводится
     к одному значению по выбранному типу аггрегации (agg_type).
    Все значения сортируются и разбиваются на интервалы одинакового размера (последний интервал забирает оставшиеся
     элементы, если их количество не делится ровно на выбранное число интервалов).

    Формат интервалов: [a, b), [b, c), [c, d) ... [e, f]

    Parameters
    ----------
    data - Датафрейм с данными
    column_name - Имя столбца с обрабатываемыми данными
    count - Количество интервалов
    agg_type - Тип округления значений внутри одного интервала (
        interval_mean - Среднее по границам интервала
        values_mean - Среднее по числам внутри интервала
        interval_max - Максимальное значение внутри интервала
    )
    verbose - Предупреждения и сообщения об ошибках выводятся в консоль

    Returns
    -------
    Датафрейм с элементами, количество уникальных значений которых уменьшено с помощью выбранного типа округления
     и разбиения на интервалы, но общее количество сохранено
    """
    data_len = len(data.index)
    agg_types = ["interval_mean", "values_mean", "interval_max"]

    if agg_type not in agg_types:
        raise Exception(f"ВНИМАНИЕ! Выбранный способ аггрегаци '{agg_type}' отсутствует в списке допустимых: {agg_types}. "
                        f"Выберите корректный способ.")

    if data_len == 0:
        print(f"ВНИМАНИЕ! Полученные данные не имеют строк для обработки.")
        return

    if count <= 0 or count != int(count):
        raise Exception(f"ВНИМАНИЕ! Количество интервалов должно быть целым положительным числом, отличным от нуля.")

    if data_len < count:
        raise Exception(f"ВНИМАНИЕ! Выбранное количество интервалов({count}) больше или равно количеству строк в " +
                        f"данных, округление невозможно. Требуется выбрать значение 'count' меньше {data_len}.")

    data_copy = data.copy()

    rows_in_interval = round(data_len // count)

    data_copy = data_copy.sort_values(axis="index", by=[column_name])
    data_copy = data_copy.reset_index(drop=True)

    for interval_num in range(count):
        begin = rows_in_interval * interval_num
        end = rows_in_interval * (interval_num + 1)
        # Последний интервал забирает оставшиеся значения
        if interval_num == count - 1:
            if agg_type == "interval_mean":
                data_copy.loc[begin:, column_name] = (data_copy.loc[begin, column_name]+data_copy.loc[data_len-1, column_name])/2
            elif agg_type == "values_mean":
                data_copy.loc[begin:, column_name] = data_copy.loc[begin:, column_name].mean()
            elif agg_type == "interval_max":
                data_copy.loc[begin:, column_name] = max(data_copy.loc[begin:, column_name])
        else:
            if agg_type == "interval_mean":
                data_copy.loc[begin:end, column_name] = (data_copy.loc[begin, column_name]+data_copy.loc[end, column_name])/2
            elif agg_type == "values_mean":
                data_copy.loc[begin:end, column_name] = data_copy.loc[begin:end, column_name].mean()
            elif agg_type == "interval_max":
                data_copy.loc[begin:end, column_name] = max(data_copy.loc[begin:end, column_name])

    return data_copy


def cut_by_threshold(data: pd.DataFrame | geopandas.GeoDataFrame,
                     column_name: str,
                     threshold: float | int,
                     is_lower: bool = True,
                     including: bool = True) -> pd.DataFrame | geopandas.GeoDataFrame:
    """
    Возвращает копию датафрейма исключая значения больше/меньше порога (threshold)

    Parameters
    ----------
    data - Датафрейм для обрезки значений
    column_name - Имя столбца с данными, по которому производится обрезка
    threshold - Пороговое значение
    is_lower - При нижнем пороге (True) отбрасывает значения ниже порога, иначе (False) отбрасывает значения выше порога
    including - При True значение порога включается в возвращаемые данные, иначе (False) отбрасывается

    Returns
    -------
    Копия датафрейма с обрезанными по порогу значениями

    """
    data_copy = data.copy()

    if is_lower:
        if including:
            return data_copy.loc[data_copy[column_name] >= threshold]
        return data_copy.loc[data_copy[column_name] > threshold]

    else:
        if including:
            return data_copy.loc[data_copy[column_name] <= threshold]
        return data_copy.loc[data_copy[column_name] < threshold]


def process_files(heightmap_file:str,
                  pollution_file: str,
                  left_bottom: Tuple[float, float],
                  target_crs: str,
                  pollutant_path: str,
                  point_pollutant_sources_path: str,
                  areal_pollutant_sources_path: str,
                  wind_data_path: str,
                  wind_data_line_number: int,
                  output_json_filename_polygons: str,
                  output_json_filename_boundary: str,
                  agg_threshold:int,
                  agg_type: str,
                  agg_count: int,
                  visualize: bool = True):

    # Чтение файла в geodataframe с сеткой точек
    geo_df_height, geo_df_height_metadata = read_grid_to_geodataframe(path=heightmap_file,
                                                                      target_crs=target_crs,
                                                                      left_bottom=left_bottom)

    geo_df_pollution, geo_df_pollution_metadata = read_grid_to_geodataframe(path=pollution_file,
                                                                            target_crs=target_crs,
                                                                            left_bottom=left_bottom)
    # Округление значений и удаление нулевых значений выбросов
    geo_df_pollution = round_pollution_values(data=geo_df_pollution,
                                              column_name="value",
                                              count=agg_count if agg_count is not None else 5,
                                              agg_type=agg_type if agg_type is not None else "interval_mean",
                                              threshold=agg_threshold if agg_threshold is not None else 1)

    geo_polygons_df_pollution = None
    geo_boundary_df_pollution = None
    if geo_df_pollution.shape[0] > 0:
        # Получение контуров из точек с одним значением
        geo_polygons_df_pollution, geo_boundary_df_pollution = parse_contours(data=geo_df_pollution,
                                                                              value_column_name="value",
                                                                              coords_column_name="coordinates",
                                                                              cellsize=geo_df_pollution_metadata[
                                                                                  "cellsize"])

        # Перевод координат в систему WGS84
        geo_polygons_df_pollution = geo_polygons_df_pollution.to_crs('EPSG:4326')
        geo_boundary_df_pollution = geo_boundary_df_pollution.to_crs('EPSG:4326')

    geo_polygons_df_height = None
    geo_boundary_df_height = None
    if geo_df_height.shape[0] > 0:
        # Получение контуров из точек с одним значением
        geo_polygons_df_height, geo_boundary_df_height = parse_contours(data=geo_df_height,
                                                                        value_column_name="value",
                                                                        coords_column_name="coordinates",
                                                                        cellsize=geo_df_height_metadata["cellsize"])

        # Перевод координат в систему WGS84
        geo_df_height = geo_df_height.to_crs('EPSG:4326')

        geo_polygons_df_height = geo_polygons_df_height.to_crs('EPSG:4326')
        geo_boundary_df_height = geo_boundary_df_height.to_crs('EPSG:4326')

    # Создание метаданных из файлов
    read_metadata = create_metadata_from_files(pollutant_path=pollutant_path,
                                               point_pollutant_sources_path=point_pollutant_sources_path,
                                               areal_pollutant_sources_path=areal_pollutant_sources_path,
                                               grid_metadata=geo_df_pollution_metadata,
                                               wind_data_path=wind_data_path,
                                               wind_data_line_number=wind_data_line_number,
                                               output_coords_in_WGS84=True)

    # Полигоны
    save_data_as_json(height_data=geo_polygons_df_height,
                      pollution_data=geo_polygons_df_pollution,
                      metadata=read_metadata,
                      output_file_name=output_json_filename_polygons)
    # Границы
    save_data_as_json(height_data=geo_boundary_df_height,
                      pollution_data=geo_boundary_df_pollution,
                      metadata=read_metadata,
                      output_file_name=output_json_filename_boundary)

    if visualize:
        # # Карта высот
        if geo_polygons_df_height is not None:
            ax = geo_polygons_df_height.plot(column="value", legend=True, alpha=0.3)
            geo_boundary_df_height.plot(ax=ax, column="value")

        # Карта выбросов
        if geo_polygons_df_pollution is not None:
            ax2 = geo_polygons_df_pollution.plot(column="value", legend=True, alpha=0.3)
            geo_boundary_df_pollution.plot(ax=ax2, column="value")

        # Карта выбросов поверх карты высот
        if geo_polygons_df_height is not None:
            ax3 = geo_polygons_df_height.plot(column="value", legend=True, alpha=0.5)
            if geo_boundary_df_pollution is not None:
                geo_boundary_df_pollution.plot(ax=ax3, column="value")

        plt.show()