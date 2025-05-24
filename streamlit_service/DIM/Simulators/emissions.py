import datetime
import random

def make_csv_emmissions(isa_count, start_date, end_date, interval, filename, path):
    # Макс сила выброса в процентах
    level = [100] * isa_count
    # Коэф. пересчета (например, в моли)
    k = [1] * isa_count

    alarm = [0] * isa_count
    duration = [0] * isa_count
    max_emissions_time = [''] * isa_count
    emission = [0] * isa_count

    rand_wind_direction = random.randint(0, 8) * 45
    threshold = 90
    start_time = str(start_date) + ' 00:00:00'
    end_time = str(end_date) + ' 00:00:00'
    current_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    # current_time = time.strptime(start_time, "%H:%M:%S")

    points_day = int(1440 // interval)

    while current_time < end_time:

        i = 0

        for j in range(isa_count):
            alarm[j] = random.randint(18, points_day)
            duration[j] = random.randint(1, 18)

        while i < points_day:
            i += 1

            for j in range(isa_count):
                if alarm[j] == i:
                    max_emissions_time[j] = current_time + datetime.timedelta(minutes=(interval * duration[j]))

            write_time = current_time.strftime("%d-%m-%Y %H:%M:%S")

            for j in range(isa_count):
                if (type(current_time) == type(max_emissions_time[j])) and (max_emissions_time[j] > current_time):
                    emission[j] = level[j] * k[j]
                else:
                    emission[j] = 0

            text = f"{write_time}"
            for counter in range(0, isa_count):
                text += f", {emission[counter]}"

            current_time = current_time+ datetime.timedelta(minutes=interval)
            with open(f'{path}/{filename}_emissoins.csv', 'a') as file:
                file.write(text)
                file.write('\n')