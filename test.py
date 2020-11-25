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
import serial
import time
import RPi.GPIO as GPIO
import base64
import codecs
import adafruit_tcs34725


path = os.path.abspath(os.path.dirname(__file__))
protoPath = os.path.join(path, "face_detector/deploy.prototxt")
modelPath = os.path.join(path, "face_detector/res10_300x300_ssd_iter_140000.caffemodel")
detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)


database = [
    {'name': 'Saif', 'tag': (136, 4, 55, 30), "phone_number":"971551234567", "eid":"784123412341234"},
    {'name': 'Ali', 'tag': (231, 176, 71, 98),"phone_number":"971507422994", "eid":"784199746027202" },
    {'name': 'Marwan', 'tag': (136, 4, 198, 181), "phone_number":"971551234567", "eid":"784123412341234"}
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
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN)
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


sensor = adafruit_tcs34725.TCS34725(i2c)


ser = serial.Serial('/dev/serial0', 9600, timeout=10)
GPIO.setup(4, GPIO.IN)
GPIO.setup(17, GPIO.OUT)


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

max_count = 2
c = 0
people_inside = []

try:
    while True:
        display.lcd_display_string("Smart Door", 1)
        display.lcd_display_string(f'{c} people inside', 2)
        sleep(1)
        display.lcd_clear()
        button_state = GPIO.input(BUTTON_PIN)
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

        if button_state:
            c-=1
            print("Button pressed")
            try:
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                sleep(3)
                GPIO.output(RELAY_PIN, GPIO.LOW)
                sleep(1)
            except KeyboardInterrupt:
                GPIO.cleanup()
            while GPIO.input(BUTTON_PIN):
                sleep(0.2)
        if status == MIFAREReader.MI_OK:
            print("card detected")
            display.lcd_display_string("card detected", 1)
            if c == max_count:
                print(f"Room full...!")
                display.lcd_display_string("Room full", 2)
                sleep(1)
                display.lcd_clear()
                continue

        (status, uid) = MIFAREReader.MFRC522_Anticoll()
        if status == MIFAREReader.MI_OK:
            print(f"Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3]))
            tag = (uid[0], uid[1], uid[2], uid[3])
            if tag not in tags:
                auth = 'Auth failed'
                auth_name = ''
                print(auth)
            for i in database:
                if i['tag'] == tag:
                    auth = 'Auth Success'
                    print(auth)
                    auth_name = i['name']
                    print(f"Welcome {auth_name}")
                    auth_phone_number = i['phone_number']
                    auth_eid = i['eid']
                    continue
            print(tag)

            # if auth_name in people_inside and auth_name!='':
            #     people_inside.remove(auth_name)
            #     continue

        ret, img = source.read()
        frame = imutils.resize(img, width=600)
        h, w = frame.shape[:2]
        imageBlob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0),
                                          swapRB=False, crop=False)

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

        if status == MIFAREReader.MI_OK:
            # display.lcd_display_string(f"{(uid[0], uid[1], uid[2], uid[3])}", 2)
            # sleep(2)
            # display.lcd_clear()
            display.lcd_display_string(auth, 2)
            sleep(1)
            display.lcd_clear()
            if not auth_name=='':
                display.lcd_display_string("Welcome Back", 1)
                display.lcd_display_string(auth_name, 2)
                sleep(1)
            amb_temp = f"Env Temp: {to_fahrenheit(mlx.ambient_temperature)}"
            obj_temp = f"Body Temp: {to_fahrenheit(mlx.object_temperature)}"
            display.lcd_clear()
            display.lcd_display_string(amb_temp, 1)
            display.lcd_display_string(obj_temp, 2)
            sleep(1)
            display.lcd_clear()
            display.lcd_display_string('MASK STATUS', 1)
            if stat is not None:
                display.lcd_display_string(str(stat), 2)
            else:
                display.lcd_display_string("No face visible", 2)
            sleep(1)
            display.lcd_clear()
            print(auth)
            print(stat)
            print(to_fahrenheit(mlx.object_temperature))
            if auth=='Auth Success' and stat=='MASK' and to_fahrenheit(mlx.object_temperature) < 100:
                display.lcd_clear()
                display.lcd_display_string("Please scan your", 1)
                display.lcd_display_string("QR code", 2)
                user_match = False
                s = input()
                s = s[0:-2]
                #s.decode("utf-8")
                if len(s)>2:
                    (r , g, b ) = sensor.color_rgb_bytes
                    print("R: " + str(r)+ ",G: " +str(g) + ",B: "+ str(b))
                    #if (g == b == 45):
                    if r >= 45:
                        print("Positive Test result")
                        testResult = False
                    else :
                        testResult = True
                        print("Negative Test Result")
                        s = base64.b64decode(s+"==")
                        s = s.decode("utf-8", "replace")
                        print(s)
                        eid = s[s.find("784"): s.find("784")+15]
                        phone_number = s[s.find("9715"): s.find("9715")+12]
                        print(eid)
                        print(phone_number)
                        if (eid == auth_eid  and phone_number == auth_phone_number ):
                            user_match = True
                else :
                    print("error in reading QRCode")
                    testResult = False
                print(s)
                time.sleep(0.2)
                if (testResult and user_match):
                    c+=1
                    print("Access Granted")
                    display.lcd_display_string("STATUS :", 1)
                    display.lcd_display_string("ACCESS GRANTED", 2)
                    people_inside.append(auth_name)
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
                    sleep(1)
                    display.lcd_clear()
            else:
                print("Access Denied")
                display.lcd_display_string("STATUS :", 1)
                display.lcd_display_string("ACCESS DENIED", 2)
                sleep(1)
                display.lcd_clear()
        sleep(1)
        print("List of people inside:", people_inside)
        if c<0: c=0

except KeyboardInterrupt:
    display.lcd_clear()
    GPIO.cleanup()
