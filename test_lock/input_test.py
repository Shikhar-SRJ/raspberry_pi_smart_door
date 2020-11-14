import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers

RELAY_PIN = 21
GPIO.setup(RELAY_PIN, GPIO.OUT) # GPIO Assign mode
while True:
    i = int(input())
    if i==0:
        try:
            GPIO.output(RELAY_PIN, GPIO.HIGH) # out
            sleep(1)
        except KeyboardInterrupt:
            GPIO.cleanup()
    elif i==1:
        try:
            GPIO.output(RELAY_PIN, GPIO.LOW) # on
            sleep(1)
        except KeyboardInterrupt:
            GPIO.cleanup()
    else:
        pass
    GPIO.cleanup()
