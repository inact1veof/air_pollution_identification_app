import datetime
import os
import tempfile
from pathlib import Path
from typing import Dict, Tuple, List
from zipfile import ZipFile

from matplotlib import pyplot as plt

from .processing_coords import (read_grid_to_geodataframe,round_pollution_values,parse_contours, read_wind_data)


def process_gralfile_response(zipfile: ZipFile,
                              paths: Dict,
                              files_dict: dict,
                              left_bottom: Tuple[float, float],
                              target_crs: str,
                              output_directory_path: str,
                              agg_threshold: int,
                              agg_type: str,
                              agg_count: int) -> Tuple[str, str]:
    show_files_paths = []

    # После выполнения блока with произойдет удаление временной директории и файлов в ней
    with tempfile.TemporaryDirectory() as tempdir:
        with zipfile as zf:
            # Проверка наличия всех файлов
            for key, path in paths.items():
                try:
                    temp_path = zf.extract(path, path=tempdir)
                    # Замена относительного пути в архиве на полный во временной директории
                    paths[key] = temp_path

                except KeyError:
                    print(f'ERROR: Did not find "{path}" in zip file')

            for path, show in files_dict.items():
                try:
                    if show:
                        temp_path = zf.extract(path, path=tempdir)
                        # Сохранение нового пути к отображаемым файлам
                        show_files_paths.append(temp_path)

                except KeyError:
                    print(f'ERROR: Did not find "{path}" in zip file')

            first = True
            output = []
            for path in show_files_paths:
                with open(path, "r") as file:
                    lines = file.readlines()
                    if first:
                        for i in range(6):
                            output.append(lines[i])
                        for k in range(6, len(lines)):
                            line = lines[k].split(" ")
                            output.append(line)
                        first = False
                    else:
                        for g in range(6, len(lines)):
                            line = lines[g].split(" ")
                            for num in range(len(line) - 1):
                                output[g][num] = str(float(output[g][num]) + float(line[num]))
            for i in range(6, len(output)):
                output[i] = " ".join(output[i])

            # Если в файле не будет строк, при визуализации уведомят об ошибке чтения файла
            filepath = ""
            Path(output_directory_path).mkdir(parents=True, exist_ok=True)
            with open(output_directory_path+"/total_concentrations.txt", "w") as file:
                file.writelines(output)
                total_concentrations_filepath = file.name

        # Обработка файлов и сохранение результата
        result_files = process_gralfile_files(heightmap_file=paths["heightmap_file_path"],
                                              pollution_file=total_concentrations_filepath,
                                              paths=paths,
                                              left_bottom=left_bottom,
                                              target_crs=target_crs,
                                              agg_threshold=agg_threshold,
                                              agg_type=agg_type,
                                              agg_count=agg_count,
                                              output_directory_path=output_directory_path)
    return result_files


def process_gralfile_files(heightmap_file: str,
                           pollution_file: str,
                           paths: Dict,
                           left_bottom: Tuple[float, float],
                           target_crs: str,
                           agg_threshold: int,
                           agg_type: str,
                           agg_count: int,
                           output_directory_path: str) -> Tuple[str, str]:
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

    # Создание графика карты выбросов поверх карты высот и легенды в текстовом файле
    path = output_directory_path + "/gralstarter_" + datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    if geo_polygons_df_height is not None:
        ax = geo_polygons_df_height.plot(column="value", alpha=0.5)
        if geo_boundary_df_pollution is not None:
            geo_boundary_df_pollution.plot(ax=ax, column="value", legend=True)

        Path(output_directory_path).mkdir(parents=True, exist_ok=True)

        plt.savefig(fname=path + ".svg",
                    format="svg")

    create_gralfile_legend_file(paths=paths,
                                legend_path=path)

    result = [None, None]
    if os.path.exists(path + ".svg"):
        result[0] = path + ".svg"
    if os.path.exists(path + ".txt"):
        result[1] = path + ".txt"

    return result[0], result[1]


def create_gralfile_legend_file(paths: Dict,
                                legend_path: str):
    with open(legend_path + ".txt", "w") as file:
        # Метеофайл
        wind_speed, wind_dir = None, None
        p = paths.get("meteopgt_path", None)
        if p is not None:
            with open(p, "r") as meteopgt_file:
                line = meteopgt_file.readlines()[-1].split(",")
                wind_speed = line[1]
                wind_dir = line[0]

        file.write(f"Wind speed (kph) = {wind_speed}\n")
        file.write(f"Wind direction (deg) = {float(wind_dir) * 10}\n")

        # Источники
        sg_dict = None
        sg_p = paths.get("sourcegroup_path", None)
        if sg_p is not None:
            sg_dict = {}
            with open(sg_p, 'r') as sg_file:
                s_lines = sg_file.readlines()
                for line in s_lines:
                    line = line.rstrip("\n").split(",")
                    sg_dict[str(line[1])] = str(line[0])

        p = paths.get("cadastre_sources_path", None)
        if p is not None:
            with open(p, "r") as cadastre_file:
                lines = cadastre_file.readlines()
                info_rows_num = 1
                sourcegroup_column_num = 10
                value_column_num = 6
                for line in range(info_rows_num, len(lines)):
                    row = lines[line].split(",")
                    source_name = None
                    source_value = row[value_column_num]
                    source_sourcegroup = row[sourcegroup_column_num]

                    if sg_dict is not None:
                        source_name = sg_dict.get(str(source_sourcegroup), None)

                    file.write(
                        f"Source value (name={source_name if source_name is not None else 'unknown'}, sgroup={source_sourcegroup}) = {source_value}\n")

        p = paths.get("point_sources_path", None)
        if p is not None:
            with open(p, "r") as point_file:
                lines = point_file.readlines()
                info_rows_num = 2
                sourcegroup_column_num = 10
                value_column_num = 3
                for line in range(info_rows_num, len(lines)):
                    row = lines[line].split(",")
                    source_name = None
                    source_value = row[value_column_num]
                    source_sourcegroup = row[sourcegroup_column_num]

                    if sg_dict is not None:
                        source_name = sg_dict[source_sourcegroup]

                    file.write(
                        f"Source value (name={source_name if source_name is not None else 'unknown'}, sgroup={source_sourcegroup}) = {source_value}\n")


# TODO добавить ввод списка коэффициентов для каждого источника или один коэф. по выбору
def edit_APsources_files_coef(Asources_path: str,
                              Psources_path: str,
                              sourcegroup_path: str,
                              source_names: List[str],
                              coef: float):
    """
    Изменяет мощность выбросов указанных источников в файлах, используемых контейнером модели.
    Справочное имя источника сверяется с именем группы источника по пути path_sourcegroup.
    Мощности источников умножаются на  введенный коэффициент.
    Исходные файлы переписываются с изменением необходимых данных в строках файлов.

    По умолчанию модель использует файлы "proj/Computation/cadastre.dat" для площадных источников (Asources)
    и "proj/Computation/point.dat" для точечных (Psources).
    Файл для path_sourcegroup хранится по пути "proj/Settings/Sourcegroups.txt".

    Parameters
    ----------
    Asources_path: - Полный путь к файлу с площадными источниками
    Psources_path: - Полный путь к файлу с точечными источниками
    sourcegroup_path - Полный путь к файлу со словарем имен и групп источников
    source_names - Список имен изменяемых источников
    coef - Коэфициент для умножения значений мощностей источников
    """
    sourcegroup_dict = {}  # sourcegroup -> name
    with open(sourcegroup_path, 'r') as file:
        s_lines = file.readlines()
        for line in s_lines:
            line = line.rstrip("\n").split(",")
            sourcegroup_dict[str(line[1])] = str(line[0])

    for f_type, path in [("asources", Asources_path), ("psources", Psources_path)]:
        info_rows_num = None
        sourcegroup_column_num = None
        value_column_num = None

        if f_type == "asources":
            info_rows_num = 1
            sourcegroup_column_num = 10
            value_column_num = 6
        elif f_type == "psources":
            info_rows_num = 2
            sourcegroup_column_num = 10
            value_column_num = 3

        edited_lines = []

        with open(path, 'r') as file:
            lines = file.readlines()

            if len(lines) > info_rows_num:
                for i in range(info_rows_num):
                    edited_lines.append(lines[i])

                for i in range(info_rows_num, len(lines)):
                    row = lines[i].split(",")
                    if sourcegroup_dict[str(row[sourcegroup_column_num])] in source_names:
                        row[value_column_num] = str(float(row[value_column_num]) * coef)
                    edited_lines.append(",".join(row))

        if len(edited_lines) > 0:
            with open(path, "w") as file:
                file.writelines(edited_lines)


def edit_APsources_files_value(Asources_path: str,
                               Psources_path: str,
                               sourcegroup_path: str,
                               source_names: List[str],
                               values: List[float]):
    """
    Изменяет мощность выбросов указанных источников в файлах, используемых контейнером модели.
    Справочное имя источника сверяется с именем группы источника по пути path_sourcegroup.
    Мощности источников заменяются на введенные значения в соответствии с порядком в списка.
    Исходные файлы переписываются с изменением необходимых данных в строках файлов.

    По умолчанию модель использует файлы "proj/Computation/cadastre.dat" для площадных источников (Asources)
    и "proj/Computation/point.dat" для точечных (Psources).
    Файл для path_sourcegroup хранится по пути "proj/Settings/Sourcegroups.txt".

    Parameters
    ----------
    Asources_path: - Полный путь к файлу с площадными источниками
    Psources_path: - Полный путь к файлу с точечными источниками
    sourcegroup_path - Полный путь к файлу со словарем имен и групп источников
    source_names - Список имен изменяемых источников
    values - Значения для замены мощностей источников
    """
    if len(source_names) != len(values):
        raise Exception("ВНИМАНИЕ! Длина списка источников не совпадает с длиной списка новых мощностей.")

    sourcegroup_dict = {}  # sourcegroup -> name
    with open(sourcegroup_path, 'r') as file:
        s_lines = file.readlines()
        for line in s_lines:
            line = line.rstrip("\n").split(",")
            sourcegroup_dict[str(line[1])] = str(line[0])

    for f_type, path in [("asources", Asources_path), ("psources", Psources_path)]:
        info_rows_num = None
        sourcegroup_column_num = None
        value_column_num = None

        if f_type == "asources":
            info_rows_num = 1
            sourcegroup_column_num = 10
            value_column_num = 6
        elif f_type == "psources":
            info_rows_num = 2
            sourcegroup_column_num = 10
            value_column_num = 3

        edited_lines = []

        with open(path, 'r') as file:
            lines = file.readlines()

            if len(lines) > info_rows_num:
                for i in range(info_rows_num):
                    edited_lines.append(lines[i])

                for i in range(info_rows_num, len(lines)):
                    row = lines[i].split(",")

                    source_name = sourcegroup_dict[str(row[sourcegroup_column_num])]
                    if source_name in source_names:
                        name_index = source_names.index(source_name)
                        row[value_column_num] = str(values[name_index])
                    edited_lines.append(",".join(row))

        if len(edited_lines) > 0:
            with open(path, "w") as file:
                file.writelines(edited_lines)


def edit_wind_file(path: str,
                   new_wind_degree: float | None,
                   new_wind_speed: float | None):
    """
        Изменяет направление и скорость ветра в указанном файле, используемом контейнером модели.
        Исходный файл переписывается с изменением необходимых данных в строках файла.

        По умолчанию модель использует файл proj/Computation/meteopgt.all

        Parameters
        ----------
        path - Путь к файлу, используемому моделью
        new_wind_degree - Новое значение направления ветра в градусах
        new_wind_speed - Новое значение скорости ветра
        """
    edited_lines = []

    with open(path, 'r') as file:
        lines = file.readlines()

        edited_lines.append(lines[0])
        edited_lines.append(lines[1])

        row = lines[2].split(",")
        if new_wind_degree is not None:
            row[0] = str(new_wind_degree / 10)
        if new_wind_speed is not None:
            row[1] = str(new_wind_speed)

        edited_lines.append(",".join(row))

    with open(path, "w") as file:
        file.writelines(edited_lines)


