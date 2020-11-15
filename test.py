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

# for camera
from camera import VideoCamera

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

cam = VideoCamera()

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
            sleep(2)
            amb_temp = f"Env Temp: {to_fahrenheit(mlx.ambient_temperature)}"
            obj_temp = f"Body Temp: {to_fahrenheit(mlx.object_temperature)}"
            display.lcd_clear()
            display.lcd_display_string(amb_temp, 1)
            display.lcd_display_string(obj_temp, 2)
            sleep(2)
            display.lcd_clear()
            display.lcd_display_string('MASK STATUS', 1)
            if cam.get_mask:
                display.lcd_display_string(str(cam.get_mask(), 2))
            else:
                display.lcd_display_string('No one here')
            sleep(2)
            display.lcd_clear()
        sleep(1)
except KeyboardInterrupt:
    display.lcd_clear()
    GPIO.cleanup()