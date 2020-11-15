import tflite_runtime.interpreter as tflite
import cv2
import numpy as np
import os
from time import sleep

global label
label = ""

base_dir = os.path.abspath(os.path.dirname(__file__))
model_path = os.path.join(base_dir, 'mask_detection.tflite')

interpreter =  tflite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

label_dict = {0:'MASK', 1:"NO MASK"}


source= cv2.VideoCapture(0)
sleep(1)

_, frame = source.read()
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

face_cls = cv2.CascadeClassifier('../facial_recognition_model.xml')
faces = face_cls.detectMultiScale(gray, 1.3, 5)

input_shape = input_details[0]['shape']
img_size = 100

label_dict = {0: 'MASK', 1: "NO MASK"}

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

def get_label():
    return label