import random
import datetime
import sched, time

def make_csv_weather(start_date, end_date, interval, filename, path):
    threshold = 90
    max_time = 15
    aver_temp = 3.3
    start_time = str(start_date) + ' 00:00:00'
    end_time = str(end_date) + ' 23:00:00'
    current_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    def print_time(current_time, threshold=None, rand_wind_speed=None):
        rand_wind_direction = 0

        k = random.randint(0, 100)
        if k > threshold:
            randSign = random.choice([-1, 1])
            rand_wind_direction = (randSign * 45 + rand_wind_direction) % 360
        last_sec = time.localtime().tm_sec
        randSign = random.choice([-1, 1])
        rand_delta_wind_speed = random.randint(0, 2)
        if (rand_delta_wind_speed * randSign + rand_wind_speed) > 6 or (
                rand_delta_wind_speed * randSign + rand_wind_speed) < 0:
            randSign = randSign * -1
        rand_wind_speed = (
                rand_delta_wind_speed * randSign + rand_wind_speed)
        if k > 80:
            rand_wind_speed = random.randint(2, 11)
        if k > 98:
            rand_wind_speed = random.randint(10, 12)
        month = current_time.month
        rand_temp = random.randint(-8, 8)
        rand_humidity = random.randint(-12, 12)
        humidity = 0
        temp = 0
        if (month == 1):
            temp = -4.3 * aver_temp + rand_temp
            humidity = 80 + rand_humidity
        if (month == 2):
            temp = -3.6 * aver_temp + rand_temp
            humidity = 79 + rand_humidity
        if (month == 3):
            temp = -1.5 * aver_temp + rand_temp
            humidity = 72 + rand_humidity
        if (month == 4):
            temp = 1.2 * aver_temp + rand_temp
            humidity = 65 + rand_humidity
        if (month == 5):
            temp = 3.3 * aver_temp + rand_temp
            humidity = 57 + rand_humidity
        if (month == 6):
            temp = 5.2 * aver_temp + rand_temp
            humidity = 68 + rand_humidity
        if (month == 7):
            temp = 5.8 * aver_temp + rand_temp
            humidity = 73 + rand_humidity
        if (month == 8):
            temp = 4.8 * aver_temp + rand_temp
            humidity = 77 + rand_humidity
        if (month == 9):
            temp = 3 * aver_temp + rand_temp
            humidity = 82 + rand_humidity
        if (month == 10):
            temp = 0.9 * aver_temp + rand_temp
            humidity = 82 + rand_humidity
        if (month == 11):
            temp = -1.8 * aver_temp + rand_temp
            humidity = 83 + rand_humidity
        if (month == 12):
            temp = -3.3 * aver_temp + rand_temp
            humidity = 83 + rand_humidity

        temp = round(temp, 2)
        write_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
        rand_pressure = random.randint(750, 770)
        rand_stability_class = random.randint(3,4)
        rand_frequency = 1.9
        text = f"{write_time}, {rand_wind_direction}, {rand_wind_speed}, {rand_stability_class}, {rand_frequency}, {rand_pressure}, {temp}, {humidity}"
        with open(f'{path}/{filename}_weather.csv', 'a') as file:
            file.write(text)
            file.write('\n')
        current_time = current_time + datetime.timedelta(minutes=interval)
        time.sleep(.1)
        return  current_time


    while current_time < end_time:
        rand_wind_speed = random.randint(0, 6)
        s = sched.scheduler(time.time, time.sleep)
        current_time = print_time(current_time, threshold, rand_wind_speed)