# for temperature sensor
import board
import busio as io
import adafruit_mlx90614
from time import sleep

# for lcd
from test_lcd import lcddriver

# for rfid
import RPi.GPIO as GPIO
from test_rfid import mfrc522 as MFRC522
import signal

display = lcddriver.lcd()

i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
mlx = adafruit_mlx90614.MLX90614(i2c)

def to_fahrenheit(celcius):
    return (9/5)*celcius + 32

continue_reading = True

def end_read(signal, frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False
    GPIO.cleanup()

signal.signal(signal.SIGINT, end_read)
MIFAREReader = MFRC522.MFRC522()


try:
    while True:
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status == MIFAREReader.MI_OK:
            print("card detected")
            display.lcd_display_string("card detected", 1)
        (status, uid) = MIFAREReader.MFRC522_Anticoll()
        if status == MIFAREReader.MI_OK:
            print("Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3]))
            display.lcd_display_string(f"{(uid[0], uid[1], uid[2], uid[3])}", 2)
            sleep(4)
        display.lcd_clear()
        amb_temp = f"Amb Temp: {to_fahrenheit(mlx.ambient_temperature)}"
        obj_temp = f"Obj Temp: {to_fahrenheit(mlx.object_temperature)}"
        display.lcd_display_string(amb_temp, 1)
        display.lcd_display_string(obj_temp, 2)
        sleep(2)
        display.lcd_clear()
        sleep(2)
except KeyboardInterrupt:
    display.lcd_clear()
    GPIO.cleanup()