"""
Ultasonic sensor detection code run on Raspberry Pi OS for collecting raw distance data within the dustbin.
"""
import requests 
import RPi.GPIO as GPIO
import time
from datetime import datetime

request = None

def remove_outlier(time_list: list[float]):
    time_list.sort()    # sort the time list
    q3 = time_list[int(0.75*len(time_list))]    # 75th percentile
    q1 = time_list[int(0.25*len(time_list))]    # 25th percentile
    iqr = q3 - q1
    for i in time_list:
        if i > q3 + 1.2*iqr or i < q1 - 1.2*iqr:
            time_list.remove(i)
    return time_list

def read_tank_info(filename):
    with open(filename, 'r') as file:
        # Read all lines from the file
        lines = file.readlines()
    height_str = lines[0]
    write_api = lines[1]
    height_list = [int(height) for height in height_str.split(',')]
    write_api_list = [api for api in write_api.split(',')]
    return height_list, write_api_list
    

try:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    
    # Pin initialization
    PIN_ECHO1 = 11
    PIN_TRIGGER1 = 12
    PIN_ECHO2 = 15
    PIN_TRIGGER2 = 16
    PIN_ECHO3 = 31
    PIN_TRIGGER3 = 32
    PIN_ECHO4 = 37
    PIN_TRIGGER4 = 38
    PIN_ECHO_list = [PIN_ECHO1, PIN_ECHO2, PIN_ECHO3, PIN_ECHO4]
    PIN_TRIGGER_list = [PIN_TRIGGER1, PIN_TRIGGER2, PIN_TRIGGER3, PIN_TRIGGER4]
    

    # Pin setup
    for pin in PIN_ECHO_list:
        GPIO.setup(pin, GPIO.IN)
    for pin in PIN_TRIGGER_list:
        GPIO.setup(pin, GPIO.OUT)
    
    # tank height list
    tank_height_list, write_api_list = read_tank_info('tankinfo.txt')
    num_tank = len(tank_height_list)
    
    while True:
        start_time = time.time()    # this is for controlling the timing
        print (f"Start new round of measuring distance")
        time_list: list[list[float]] = [[] for _ in range(num_tank)]
        
        for i in range(10):
            for j in range(num_tank):
                time.sleep(0.2)     # waiting for sensor to settle down
                GPIO.output(PIN_TRIGGER_list[j], GPIO.HIGH)
                time.sleep(0.0001)
                GPIO.output(PIN_TRIGGER_list[j], GPIO.LOW)
                while GPIO.input(PIN_ECHO_list[j])==0:
                    pulse_start_time = time.time()
                while GPIO.input(PIN_ECHO_list[j])==1:
                    pulse_end_time = time.time()
                pulse_duration = pulse_end_time - pulse_start_time
                time_list[j].append(pulse_duration)
        
        for i in range(num_tank):
            time_list[i] = remove_outlier(time_list[i])    # sort the time list and remove outlier
            median_index = int(0.5*len(time_list[i]))
            data_range = int(0.2*len(time_list[i]))/2     # 20% of the data range
            median_10_data = time_list[i][median_index-data_range:median_index+data_range]
            median_10_avg = sum(median_10_data) / len(median_10_data)
            ultra_distance = max(tank_height_list[i], round(median_10_avg* 17150, 2)) # distance detected by ultrasonic sensor
            print (f"Distance tank {i}:",ultra_distance,"cm")
            # fullness = round((tank_height_list[i]-ultra_distance)/tank_height_list[i]*100,2)
            # print(f"Fullness tank {i}: {fullness}")
            print(f"Sending data tank {i} to ThingSpeak")
            RequestToThingspeak = f'https://api.thingspeak.com/update?api_key={write_api_list[i]}&field1='
            RequestToThingspeak += str(ultra_distance)
            request = requests.get(RequestToThingspeak)
            print(request.text)
            
        print("Waiting 15 seconds before next measurement")
        end_time = time.time()
        time_taken = end_time - start_time
        sleep_time = max(0, 15 - time_taken)
        # take into account of the measurement time
        time.sleep(sleep_time)
        
finally:
    GPIO.cleanup()


# print('Sending to ThingSpeak')
# RequestToThingspeak = 'https://api.thingspeak.com/update?api_key=LISTAUKF24AX59FX&field1='
# RequestToThingspeak += str(fullness)
# request = requests.get(RequestToThingspeak)
# print(request.text)