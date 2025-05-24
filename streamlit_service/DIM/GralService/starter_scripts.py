import os
import time
from typing import Dict, Tuple

from .processing import (process_gralfile_response,edit_wind_file,edit_APsources_files_coef,edit_APsources_files_value)
from .request_functions import gralfile_get
from .processing_coords import MSK_74_CRS_TEST


def gral_starter_script(url: str,
                        port: int | str,
                        left_bottom: Tuple[float, float],
                        target_crs: str,
                        output_directory_path: str,
                        path_dict: Dict[str, str] | None = None,
                        show_sources_dict: Dict[str, bool] | None = None,
                        agg_threshold: int = 1,
                        agg_type: str = "interval_max",
                        agg_count: int = 5,
                        edit_APsources_coef_dict: Dict | None = None,
                        edit_APsources_value_dict: Dict | None = None,
                        edit_wind_value_dict: Dict | None = None
                        ) -> Tuple[str, str]:
    """
    Изменение данных в папке контейнера модели при наличии словарей
     с параметрами (edit_..._dict) и запуск запроса к GRAL модели.
    Результат работы функции сохраняется по указанному пути (output_directory_path)
     с именем формата "gralstarter_{datetime}.png/.txt".

        Пример словаря для edit_APsources_coef:
            edit_APsources_coef_dict = {
                "Asources_path": "C:/ ... /proj/Computation/cadastre.dat",
                "Psources_path": "C:/ ... /proj/Computation/point.dat",
                "sourcegroup_path": "C:/ ... /proj/Settings/Sourcegroups.txt",
                "source_names": ["156", "0010"],
                "coef": 10
            }
        Пример словаря для edit_APsources_value:
            edit_APsources_value_dict = {
                "Asources_path": "C:/ ... /proj/Computation/cadastre.dat",
                "Psources_path": "C:/ ... /proj/Computation/point.dat",
                "sourcegroup_path": "C:/ ... /proj/Settings/Sourcegroups.txt",
                "source_names": ["156", "0010"],
                "values": [0.5, 0.12]
            }
        Пример словаря для edit_wind_value:
            edit_wind_value_dict = {
                "path": "C:/ ... /proj/Computation/meteopgt.all",
                "new_wind_degree": 0,
                "new_wind_speed": 0.3
            }

    Parameters
    ----------
    url - Адрес контейнера модели, например "http://localhost"
    port - Порт для подключения к контейнеру модели, например 5000
    left_bottom - Координаты левого нижнего угла сетки в широте и долготе
    target_crs - Формула местной системы координат
    path_dict - Словарь с путями к файлам в архиве
    show_sources_dict - Словарь с путями к файлам выбросов источников и булевым параметрам отображения файла
    wind_data_line_number - Номер строки в файле, которую следует использовать для получения данных, начиная с 1
     Последняя строка файла = -1
    agg_threshold - Граница разделения данных для округления значений выбросов
    agg_type - Тип округления значений внутри одного интервала
    agg_count - Количество интервалов ниже границы
    output_json_filename_polygons - Имя и путь для сохранения JSON результата, полигоны
    output_json_filename_boundary - Имя и путь для сохранения JSON результата, границы
    visualize - Отрисовывать ли график в приложении (не влияет на сохранение выходных изображений)
    edit_APsources_coef_dict - Словарь с параметрами для изменения данных об источниках (умножение на коэффициент),
     при отсутствии данные не будут изменены
     Все поля словаря обязательны!
    edit_APsources_value_dict - Словарь с параметрами для изменения данных об источниках (замена значений),
     при отсутствии данные не будут изменены
     Все поля словаря обязательны!
    edit_wind_value_dict - Словарь с параметрами для изменения данных о ветре (замена значений),
     при отсутствии данные не будут изменены
     Можно передавать только один из параметров в словаре, другой не будет изменен.

    Returns
    -------
    Путь к результату работы функции, изображению и файлу с легендой и параметрами запроса

    """
    total_func_time_start = time.time()
    URL = f"{url}:{port}"

    if path_dict is None:
        path_dict = {
            "heightmap_file_path": os.getenv("ZIP_HEIGHTMAP"),
            "cadastre_sources_path": os.getenv("ZIP_CADASTRE"),
            "point_sources_path": os.getenv("ZIP_POINT"),
            "sourcegroup_path": os.getenv("ZIP_SOURCEGROUPS"),
            "meteopgt_path": os.getenv("ZIP_METEOPGT")
        }

    # Параметры отрисовки источников на графике
    if show_sources_dict is None:
        show_sources_dict = {"soft/Project/Computation/00001-101.txt": True,
                             "soft/Project/Computation/00001-102.txt": True,
                             "soft/Project/Computation/00001-104.txt": True,
                             "soft/Project/Computation/00001-105.txt": True,
                             "soft/Project/Computation/00001-106.txt": True,
                             "soft/Project/Computation/00001-107.txt": True,
                             "soft/Project/Computation/00001-108.txt": True,
                             "soft/Project/Computation/00001-109.txt": True,
                             "soft/Project/Computation/00001-110.txt": True,
                             "soft/Project/Computation/00001-111.txt": True,
                             "soft/Project/Computation/00001-112.txt": True,
                             "soft/Project/Computation/00001-113.txt": True,
                             "soft/Project/Computation/00001-114.txt": True,
                             "soft/Project/Computation/00001-115.txt": True}

    # Изменение файлов
    if edit_APsources_coef_dict is not None:
        edit_APsources_files_coef(
            Asources_path=edit_APsources_coef_dict["Asources_path"],
            Psources_path=edit_APsources_coef_dict["Psources_path"],
            sourcegroup_path=edit_APsources_coef_dict["sourcegroup_path"],
            source_names=edit_APsources_coef_dict["source_names"],
            coef=edit_APsources_coef_dict["coef"])

    if edit_APsources_value_dict is not None:
        edit_APsources_files_value(
            Asources_path=edit_APsources_value_dict["Asources_path"],
            Psources_path=edit_APsources_value_dict["Psources_path"],
            sourcegroup_path=edit_APsources_value_dict["sourcegroup_path"],
            source_names=edit_APsources_value_dict["source_names"],
            values=edit_APsources_value_dict["values"])

    if edit_wind_value_dict is not None:
        edit_wind_file(
            path=edit_wind_value_dict["path"],
            new_wind_degree=edit_wind_value_dict.get("new_wind_degree", None),
            new_wind_speed=edit_wind_value_dict.get("new_wind_speed", None)
        )

    gral_start_time = time.time()

    # Получение архива http запросом
    zipfile = gralfile_get(URL)

    zipfile.extractall('DIM/GralService/output/calc_files')
    '''
    gral_end_time = time.time()
    gral_calculation_time = gral_end_time - gral_start_time

    # Вызов функции для обработки файлов архива, сохранения данных в JSON и визуализации графиков
    result_files = process_gralfile_response(zipfile=zipfile,
                                             paths=path_dict,
                                             files_dict=show_sources_dict,
                                             left_bottom=left_bottom,
                                             target_crs=target_crs,
                                             output_directory_path=output_directory_path,
                                             agg_threshold=agg_threshold,
                                             agg_type=agg_type,
                                             agg_count=agg_count)

    total_func_time_end = time.time()
    total_func_time = total_func_time_end - total_func_time_start

    if result_files[1] is not None:
        with open(result_files[1], "a") as file:
            file.write(f"GRAL calculation time (sec): {round(gral_calculation_time, 2)}\n")
            file.write(f"Total function execution time (sec): {round(total_func_time, 2)}\n")

            for key, value in show_sources_dict.items():
                file.write(f"show {key}: {value}\n")
    
    return result_files
    '''

def script_360_wind_rotation_test():
    # ВНИМАНИЕ! Необходимо указать/передать правильный путь к файлу (edit_wind_value_dict),
    # который используется моделью в докер контейнере в .env
    for wind_degree in range(0, 360, 30):

        # new_wind_degree в словаре отсутствует - будет изменено только направление ветра
        gral_starter_script(url=os.getenv("URL"),
                            port=os.getenv("PORT"),
                            left_bottom=(float(os.getenv("LEFT_BOTTOM_X")), float(os.getenv("LEFT_BOTTOM_Y"))),
                            target_crs=MSK_74_CRS_TEST,
                            output_directory_path=os.getenv("OUTPUT_DIRECTORY"),
                            edit_wind_value_dict={
                                "path": os.getenv("METEOPGT"),
                                "new_wind_degree": wind_degree,
                                # "new_wind_speed": 0.83
                            })

def script_show_different_sources_test():
    # ВНИМАНИЕ! Необходимо отображать хотя бы один источник в show_sources_dict
    for source_to_show in range(14):
        test = [False if i != source_to_show else True for i in range(0, 14)]

        gral_starter_script(url=os.getenv("URL"),
                            port=os.getenv("PORT"),
                            left_bottom=(float(os.getenv("LEFT_BOTTOM_X")), float(os.getenv("LEFT_BOTTOM_Y"))),
                            target_crs=MSK_74_CRS_TEST,
                            output_directory_path=os.getenv("OUTPUT_DIRECTORY"),
                            show_sources_dict={"soft/Project/Computation/00001-101.txt": test[0],
                                               "soft/Project/Computation/00001-102.txt": test[1],
                                               "soft/Project/Computation/00001-104.txt": test[2],
                                               "soft/Project/Computation/00001-105.txt": test[3],
                                               "soft/Project/Computation/00001-106.txt": test[4],
                                               "soft/Project/Computation/00001-107.txt": test[5],
                                               "soft/Project/Computation/00001-108.txt": test[6],
                                               "soft/Project/Computation/00001-109.txt": test[7],
                                               "soft/Project/Computation/00001-110.txt": test[8],
                                               "soft/Project/Computation/00001-111.txt": test[9],
                                               "soft/Project/Computation/00001-112.txt": test[10],
                                               "soft/Project/Computation/00001-113.txt": test[11],
                                               "soft/Project/Computation/00001-114.txt": test[12],
                                               "soft/Project/Computation/00001-115.txt": test[13]}
                            )


def script_set_source_value_test():
    # ВНИМАНИЕ! Необходимо указать/передать правильные пути к файлам (edit_APsources_value_dict),
    # которые используются моделью в докер контейнере в .env
    # Файл sourcegroup_path не обязателен, он отвечает за данные сорс группы источника в текстовой легенде
    gral_starter_script(url=os.getenv("URL"),
                        port=os.getenv("PORT"),
                        left_bottom=(float(os.getenv("LEFT_BOTTOM_X")), float(os.getenv("LEFT_BOTTOM_Y"))),
                        target_crs=MSK_74_CRS_TEST,
                        output_directory_path=os.getenv("OUTPUT_DIRECTORY"),
                        edit_APsources_value_dict={
                            "Asources_path": os.getenv("CADASTRE_SOURCES"),
                            "Psources_path": os.getenv("POINT_SOURCES"),
                            "sourcegroup_path": os.getenv("SOURCEGROUPS"),
                            "source_names": ["156", "0010"],
                            "values": [11, 22]
                        }
                        )


def script_set_source_coef_test():
    # ВНИМАНИЕ! Необходимо указать/передать правильные пути к файлам (edit_APsources_value_dict),
    # которые используются моделью в докер контейнере в .env
    # Файл sourcegroup_path не обязателен, он отвечает за данные сорс группы источника в текстовой легенде
    gral_starter_script(url=os.getenv("URL"),
                        port=os.getenv("PORT"),
                        left_bottom=(float(os.getenv("LEFT_BOTTOM_X")), float(os.getenv("LEFT_BOTTOM_Y"))),
                        target_crs=MSK_74_CRS_TEST,
                        output_directory_path=os.getenv("OUTPUT_DIRECTORY"),
                        edit_APsources_coef_dict={
                            "Asources_path": os.getenv("CADASTRE_SOURCES"),
                            "Psources_path": os.getenv("POINT_SOURCES"),
                            "sourcegroup_path": os.getenv("SOURCEGROUPS"),
                            "source_names": ["156", "0010"],
                            "coef": 100
                        }
                        )