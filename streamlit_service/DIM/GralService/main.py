import os
from dotenv import load_dotenv

from DIM.GralService.starter_scripts import (gral_starter_script,
                              script_360_wind_rotation_test,
                              script_show_different_sources_test,
                              script_set_source_value_test,
                              script_set_source_coef_test)
from DIM.GralService.processing_coords import MSK_74_CRS_TEST



def run_gral(source_names, coef):
    load_dotenv(dotenv_path="DIM/GralService/.env")
    gral_starter_script(url=os.getenv("URL"),
                        port=os.getenv("PORT"),
                        left_bottom=(float(os.getenv("LEFT_BOTTOM_X")), float(os.getenv("LEFT_BOTTOM_Y"))),
                        target_crs=MSK_74_CRS_TEST,
                        output_directory_path=os.getenv("OUTPUT_DIRECTORY"),
                        edit_APsources_coef_dict={
                            "Asources_path": os.getenv("CADASTRE_SOURCES"),
                            "Psources_path": os.getenv("POINT_SOURCES"),
                            "sourcegroup_path": os.getenv("SOURCEGROUPS"),
                            "source_names": source_names,
                            "coef": coef
                        }
                        )

if __name__ == "__main__":
    load_dotenv(dotenv_path=".env")

    # Пример запуска скрипта с параметрами по умолчанию (пути к файлам, без изменений в данных)
    res = gral_starter_script(url=os.getenv("URL"),
                              port=os.getenv("PORT"),
                              left_bottom=(float(os.getenv("LEFT_BOTTOM_X")), float(os.getenv("LEFT_BOTTOM_Y"))),
                              target_crs=MSK_74_CRS_TEST,
                              output_directory_path=os.getenv("OUTPUT_DIRECTORY"))
    # Запуск тестового скрипта с перебором направлений ветра (12 вызовов)
    # script_360_wind_rotation_test()

    # Запуск тестового скрипта с перебором показываемых источников (14 вызовов)
    # Некоторые источники могут не показывть выброс из-за особенностей округления значений при обработке
    script_show_different_sources_test()

    # Запуск тестового скрипта с заменой значений двух источников в файлах перед рассчетом
    # script_set_source_value_test()

    # Запуск тестового скрипта с умножением значений двух источников в файлах перед рассчетом
    # script_set_source_coef_test()