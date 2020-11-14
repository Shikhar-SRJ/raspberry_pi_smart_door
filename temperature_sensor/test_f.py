import board
import busio as io
import adafruit_mlx90614
from time import sleep

# the mlx90614 must be run at 100k [normal speed]
# i2c default mode is is 400k [full speed]
# the mlx90614 will not appear at the default 400k speed
i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
mlx = adafruit_mlx90614.MLX90614(i2c)


#convert in fahrenheit
def to_fahrenheit(celcius):
    return((9/5)*celcius + 32)

# temperature results in celsius
while True:
    print("Ambent Temp: ", to_fahrenheit(mlx.ambient_temperature))
    print("Object Temp: ", to_fahrenheit(mlx.object_temperature))
    print("")
    sleep(1)

