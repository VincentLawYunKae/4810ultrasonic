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

try:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    
    # Pin initialization
    PIN_TRIGGER = 7
    PIN_ECHO = 11

    # Pin setup
    GPIO.setup(PIN_TRIGGER, GPIO.OUT)
    GPIO.setup(PIN_ECHO, GPIO.IN)
    dustbin_height = int(input("Enter the height of the dustbin (in cm): "))
    print("Offset height = sensor height - dustbin height (Please obtain this through your own experiment)")
    offset_height = int(input("Enter the offset height (in cm): "))
    last_distance = None
    first_loop_done = False
    tag = input("Enter the tag of the dustbin: ")
    
    while True:
        start_time = time.time()
        print ("Start measuring distance")
        time_list = []
        # collect 30 measurements
        for i in range(100):
            time.sleep(0.2)     # waiting for sensor to settle down
            # set up a 10us pulse on trigger pin
            GPIO.output(PIN_TRIGGER, GPIO.HIGH) 
            time.sleep(0.00001)
            GPIO.output(PIN_TRIGGER, GPIO.LOW)
            # wait for echo pin to go high
            while GPIO.input(PIN_ECHO)==0:
                pulse_start_time = time.time()
            while GPIO.input(PIN_ECHO)==1:
                pulse_end_time = time.time()
            # calculate the duration of the pulse
            pulse_duration = pulse_end_time - pulse_start_time
            time_list.append(pulse_duration)
        time_list = remove_outlier(time_list)    # sort the time list
        # print(time_list)
        # Using median 10 average method to filter out the outliers and ensure accuracy
        median_index = int(0.5*len(time_list))
        median_10_data = time_list[median_index-5:median_index+5]
        # print(median_10_data)
        median_10_avg = sum(median_10_data) / len(median_10_data)
        ultra_distance = round(median_10_avg* 17150, 2)     # distance detected by ultrasonic sensor
        #prevent overflow
        max_ultradist = offset_height + dustbin_height
        min_ultradist = offset_height 
        #overflow scenario
        if ultra_distance < min_ultradist:
            ultra_distance = min_ultradist
        # empty scenario
        elif ultra_distance > max_ultradist:
            ultra_distance = max_ultradist
        
        print ("Distance:",ultra_distance,"cm")
        dustbin_distance = round(ultra_distance-offset_height, 2)
        fullness = round((dustbin_height-dustbin_distance)/dustbin_height*100,2)
        print(f"Fullness: {fullness}")

        # upload data to csv file
        if first_loop_done:
            roc = round(fullness - last_fullness, 2)
        else:
            roc = 0
            first_loop_done = True
        with open('data.csv', 'a') as f:
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute
            time_value = current_hour * 60 + current_minute
            line = str(time_value) + "," + str(fullness) + "," + str(roc) + "," + tag + "\n"
            f.write(line)
        last_fullness = fullness
        print("Waiting 1 minutes before next measurement") 
        # take into account of the measurement time
        # time.sleep(0.5)         # for testing purpose
        end_time = time.time()
        time_taken = end_time - start_time
        time.sleep(60 - time_taken)
        
finally:
    GPIO.cleanup()


# print('Sending to ThingSpeak')
# RequestToThingspeak = 'https://api.thingspeak.com/update?api_key=LISTAUKF24AX59FX&field1='
# RequestToThingspeak += str(fullness)
# request = requests.get(RequestToThingspeak)
# print(request.text)