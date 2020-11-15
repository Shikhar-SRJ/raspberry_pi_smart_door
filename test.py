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
import tflite_runtime.interpreter as tflite
import cv2
import numpy as np
import os


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

model_path = '/home/pi/pro/tflite/mask_detection.tflite'
interpreter = tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
label_dict = {0:'MASK', 1:"NO MASK"}

source = cv2.VideoCapture(0)
sleep(1)

try:
    while True:
        ret, frame = source.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        face_cls = cv2.CascadeClassifier('facial_recognition_model.xml')
        faces = face_cls.detectMultiScale(gray, 1.3, 5)

        input_shape = input_details[0]['shape']
        img_size = 100

        label_dict = {0: 'MASK', 1: "NO MASK"}
        stat = None
        for x, y, w, h in faces:
            face_img = gray[y:y + h, x:x + w]
            resized = cv2.resize(face_img, (img_size, img_size))
            normalized = resized / 255.0
            reshaped = np.reshape(normalized, input_shape)
            reshaped = np.float32(reshaped)
            interpreter.set_tensor(input_details[0]['index'], reshaped)
            interpreter.invoke()
            result = interpreter.get_tensor(output_details[0]['index'])
            label = np.argmax(result, axis=1)[0]
            stat = label_dict[label]

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
            if stat is not None:
                display.lcd_display_string(str(stat), 2)
            else:
                display.lcd_display_string("No one is here", 2)
            sleep(2)
            display.lcd_clear()
        sleep(1)
except KeyboardInterrupt:
    display.lcd_clear()
    GPIO.cleanup()
    source.release()