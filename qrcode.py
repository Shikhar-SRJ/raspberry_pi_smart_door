import serial
import time
import RPi.GPIO as GPIO
import base64
import codecs
import board
import busio 
import adafruit_tcs34725

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_tcs34725.TCS34725(i2c)


ser = serial.Serial('/dev/serial0', 9600, timeout=10)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)
GPIO.setup(17, GPIO.OUT)

while False:
    GPIO.output(17, GPIO.input(4))
    
try:
    while True:
        s = input()
        s = s[0:-2]
        #s.decode("utf-8")
        if len(s)>2:
            (r , g, b ) = sensor.color_rgb_bytes
            print("R: " + str(r)+ ",G: " +str(g) + ",B: "+ str(b))
            #if (g == b == 45):
            if r == 45:
                print("Positive Test result")
            else :
                print("Negative Test Result")
            s = base64.b64decode(s+"==")
            s = s.decode("utf-8", "replace")
            print(s)
            eid = s[s.find("784"): s.find("784")+15]
            phone_number = s[s.find("9715"): s.find("9715")+12]
            print(eid)
            print(phone_number)
        print(s)
        time.sleep(0.2)
finally:
    ser.close()
    
    
x = "RUE2RDRDMDE5OTpxci1hZG1pbi1yZWFkZXIxOjAwMDdDMUJBOEU4Q0IyOUQwNjg1RkJDRkMzMDdDMjc4:Nzg0MTk5NTg0ODc5NzYzXzk3MTU1NDU0NjQ4MDowODRkYWloaTZqbXR2ajZ2aGZ0cjozRTFCRUVFNjc4NDZFNjkzRTI2RTZDRERFODIz"