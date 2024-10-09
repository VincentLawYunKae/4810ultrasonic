"""
Ultasonic sensor detection code run on Raspberry Pi OS for collecting raw distance data within the
dustbin.
"""
import requests
import RPi.GPIO as GPIO
import time
request = None

try:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    # Pin initialization
    PIN_TRIGGER = 7
    PIN_ECHO = 11
    # Pin setup
    GPIO.setup(PIN_TRIGGER, GPIO.OUT)
    GPIO.setup(PIN_ECHO, GPIO.IN)
    
    
    while True:
        print ("Start measuring distance")
        time_list = []
        # collect 30 measurements
        for i in range(30):
            time.sleep(0.2) # waiting for sensor to settle down
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
        time_list.sort() # sort the time list
        # Using median 10 average method to filter out the outliers and ensure accuracy
        median_10_data = time_list[10:20]
        median_10_avg = sum(median_10_data) / len(median_10_data)
        distance = round(median_10_avg* 17150, 2)
        print ("Distance:",distance,"cm")
        # upload data to Thingspeak
        print('Sending to ThingSpeak')
        RequestToThingspeak = 'https://api.thingspeak.com/update?api_key=LISTAUKF24AX59FX&field1='
        RequestToThingspeak += str(distance)
        request = requests.get(RequestToThingspeak)
        print(request.text)
        print("Waiting 15 seconds before next measurement")
        # take into account of the measurement time
        time.sleep(8.9997)
        
finally:
    GPIO.cleanup()