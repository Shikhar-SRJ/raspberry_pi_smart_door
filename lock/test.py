import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM) # GPIO Numbers instead of board numbers

RELAIS_1_GPIO = 21
GPIO.setup(RELAIS_1_GPIO, GPIO.OUT) # GPIO Assign mode

try:
    GPIO.output(RELAIS_1_GPIO, GPIO.HIGH) # out
    sleep(1)
    GPIO.output(RELAIS_1_GPIO, GPIO.LOW) # on
    sleep(1)
    GPIO.cleanup()
except KeyboardInterrupt:
    GPIO.cleanup()
