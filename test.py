import board
import busio as io
import adafruit_mlx90614
from time import sleep

from test_lcd import lcddriver

i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
mlx = adafruit_mlx90614.MLX90614(i2c)

display = lcddriver.lcd()

def to_fahrenheit(celcius):
    return((9/5)*celcius + 32)

try:
    while True:
        amb_temp = f"Ambent Temp: {to_fahrenheit(mlx.ambient_temperature)}"
        obj_temp = f"Object Temp: {to_fahrenheit(mlx.object_temperature)}"
        display.lcd_display_string(amb_temp, 1)
        display.lcd_display_string(obj_temp, 2)
        sleep(2)
        display.lcd_clear()
        sleep(2)
except KeyboardInterrupt:
    display.lcd_clear()