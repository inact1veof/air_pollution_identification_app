import os
import shutil

from DIM.GralService.main import run_gral


def get_source_names():
    current_directory = os.getcwd()
    with open(f'DIM/GralService/power_files/Sourcegroups.txt', 'r') as file:
        lines = file.readlines()
    result_dict = {}
    for line in lines:
        line = line.strip()
        key, value = line.split(',')
        result_dict[int(value)] = str(key)
    return result_dict

def get_moving_filenames():
    with open('DIM/GralService/power_files/calculation_filenames.txt', 'r') as file:
        lines = file.readlines()
    result = []
    for line in lines:
        line = line.strip()
        result.append(str(line))
    return result

def run_normal():
    sources = list(get_source_names().values())
    run_gral(sources, 1)
    target_dir = f'web_app/calculation_files/00_normal'

    move_txt_to_calc(target_dir)

def run_abnormal(source_name, coef):
    run_gral([source_name], coef)

def move_txt_to_calc(moving_dir):
    filenames = get_moving_filenames()

    if not os.path.exists(moving_dir):
        os.makedirs(moving_dir)
    else:
        for filename in os.listdir(moving_dir):
            file_path = os.path.join(moving_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    from_dir = 'DIM/GralService/output/calc_files/soft/Project/Computation'

    for file_name in filenames:
        source_file = os.path.join(from_dir, file_name)
        if os.path.isfile(source_file):
            shutil.move(source_file, moving_dir)

def make_caclulation_list(n):
    sources = get_source_names()

    for key, value in sources.items():
        if key <= 9:
            folder_num = f'0{str(key)}'
        else:
            folder_num = str(key)
        target_dir = f'web_app/calculation_files/{folder_num}_source'

        run_abnormal(value, n)
        print(f'running into:[{target_dir}] | with multiple: {n}')
        move_txt_to_calc(target_dir)

        run_abnormal(value, float(1/n))
        print(f'running hold | with multiple: {float(1/n)}')