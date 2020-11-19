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
import imutils
import numpy as np
import os

path = os.path.abspath(os.path.dirname(__file__))
protoPath = os.path.join(path, "face_detector/deploy.prototxt")
modelPath = os.path.join(path, "face_detector/res10_300x300_ssd_iter_140000.caffemodel")
detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)


database = [
    {'name': 'Ali', 'tag': (136, 4, 55, 30)},
    {'name': 'Saif', 'tag': (231, 176, 71, 98)},
    {'name': 'Marwan', 'tag': (136, 4, 198, 181)},
]

tags = []
for i in database:
    tags.append(i['tag'])


display = lcddriver.lcd()

i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
mlx = adafruit_mlx90614.MLX90614(i2c)

RELAY_PIN = 21
BUTTON_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)

def to_fahrenheit(celcius):
    return (9/5)*celcius + 32

continue_reading = True

def end_read(signal, frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False
    GPIO.cleanup()
    source.release()

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

c = 0
try:
    while True:
        ret, img = source.read()
        frame = imutils.resize(img, width=600)
        h, w = frame.shape[:2]
        imageBlob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0), swapRB=False, crop=False)

        input_shape = input_details[0]['shape']
        img_size = 224

        label_dict = {0: 'MASK', 1: "NO MASK"}
        stat = None

        # apply OpenCV's deep learning-based face detector to localize
        # faces in the input image
        detector.setInput(imageBlob)
        detections = detector.forward()

        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with
            # the prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections
            if confidence > 0.5:
                # compute the (x, y)-coordinates of the bounding box for
                # the face
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # extract the face ROI
                face = frame[startY:endY, startX:endX]
                (fH, fW) = face.shape[:2]

                # ensure the face width and height are sufficiently large
                if fW < 20 or fH < 20:
                    continue

                # construct a blob for the face ROI, then pass the blob
                # through our face embedding model to obtain the 128-d
                # quantification of the face
                faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)

                resized = cv2.resize(frame, (img_size, img_size))
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
            tag = (uid[0], uid[1], uid[2], uid[3])
            if tag not in tags:
                auth = 'Auth failed'
                auth_name = ''
                print(auth)
            for i in database:
                if i['tag']==tag:
                    auth = 'Auth Success'
                    print(auth)
                    auth_name = i['name']
                    print(f"Welcome {auth_name}")
                    continue
            print(tag)
            # display.lcd_display_string(f"{(uid[0], uid[1], uid[2], uid[3])}", 2)
            # sleep(2)
            # display.lcd_clear()
            display.lcd_display_string(auth, 2)
            sleep(2)
            display.lcd_clear()
            if not auth_name=='':
                display.lcd_display_string("Welcome Back", 1)
                display.lcd_display_string(auth_name, 2)
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
                display.lcd_display_string("No face visible", 2)
            sleep(2)
            display.lcd_clear()
            print(auth)
            print(stat)
            print(to_fahrenheit(mlx.object_temperature))
            if auth=='Auth Success' and stat=='MASK' and to_fahrenheit(mlx.object_temperature) < 100:
                c+=1
                print("Access Granted")
                display.lcd_display_string("STATUS :", 1)
                display.lcd_display_string("ACCESS GRANTED", 2)
                try:
                    GPIO.output(RELAY_PIN, GPIO.HIGH)
                    sleep(5)
                    GPIO.output(RELAY_PIN, GPIO.LOW)
                    sleep(1)
                except KeyboardInterrupt:
                    GPIO.cleanup()
                display.lcd_clear()
            else:
                print("Access Denied")
                display.lcd_display_string("STATUS :", 1)
                display.lcd_display_string("ACCESS DENIED", 2)
                sleep(2)
                display.lcd_clear()
        sleep(1)
        button_state = GPIO.input(BUTTON_PIN)
        if not button_state:
            c-=1
            print("button pressed")
            try:
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                sleep(5)
                GPIO.output(RELAY_PIN, GPIO.LOW)
                sleep(1)
            except KeyboardInterrupt:
                GPIO.cleanup()
            while not GPIO.input(BUTTON_PIN):
                sleep(0.2)
        sleep(1)
except KeyboardInterrupt:
    display.lcd_clear()
    GPIO.cleanup()
